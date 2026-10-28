"""Jurisdiction, migrations and real transactional locality planning regression tests."""
from datetime import datetime,timedelta,timezone
from io import BytesIO
import json
import pytest
from PIL import Image
from backend.db.connection import connection
from backend.db import repository as repo
from backend.services.administration import provision,verify_password,identity
from backend.optimizer import plan_localities


def image():
    out=BytesIO();Image.new('RGB',(12,12),'blue').save(out,format='PNG');return out.getvalue()


def report(client,pin='110001',title='Blocked roadside drain',people=None):
    data={'city_id':'delhi','title':title,'category':'drainage','location':'Recorded locality near market','description':'Drain is blocked and needs an officer inspection.','postal_code':pin,'email':'resident@example.com','reported_damage_priority':'Critical'}
    if people is not None:data['reported_affected_people_count']=str(people)
    return client.post('/api/civic/reports',data=data,files=[('images',('issue.png',image(),'image/png'))])


def officer(client,pin='110001',username='pin-officer'):
    profile=provision(username,'Test-password-2026','PIN reviewing officer','officer',[pin])
    response=client.post('/api/auth/login',json={'username':username,'password':'Test-password-2026'})
    assert response.status_code==200
    return profile


def pool(client,pin='110001',budget=100000):
    now=datetime.now(timezone.utc)
    payload={'city_id':'delhi','pincode':pin,'department':'Drainage response','service_area':'PIN '+pin,'specialization':'Drain work','workers_on_shift':20,'workers':20,'crews':10,'pumps':10,'vehicles':10,'budget':budget,'crew_hours':{'water':20,'road':20,'drain':20},'source_ref':'Test authorized roster','valid_from':(now-timedelta(hours=1)).isoformat(),'valid_until':(now+timedelta(hours=8)).isoformat()}
    response=client.post('/api/resources/pools',json=payload)
    assert response.status_code==201,response.text
    return response.json()


def review(client,identifier,population=100):
    return client.post('/api/civic/review/'+identifier,json={'validation':'valid','status':'under_review','urgency':'urgent','department':'Drainage','damage_priority':'Critical','affected_people_count':population,'population_basis':'estimated' if population is not None else 'unknown','intervention_cost':5000,'crew_type':'drain','required_crews':1,'required_workers':2,'required_vehicles':1,'required_pumps':0,'duration_hours':1})


def funding(client,pool):
    response=client.post('/api/locality-planning/budgets',json={'city_id':'delhi','pincode':'110001','pool_id':pool['id'],'budget':10000,'fiscal_year':'2026–27','source_ref':'Authorized exercise funding'})
    assert response.status_code==201,response.text
    return response.json()


def test_postal_migration_coverage_and_original_records_preserved(client):
    expected={'delhi':77,'chandigarh':24,'chennai':2}
    existing=repo.append('complaint',{'city_id':'delhi','postal_code':'110001','description':'Preserved legacy record','status':'submitted'})
    repo.initialize()
    assert repo.get('complaint',existing['id'])['description']=='Preserved legacy record'
    for city,count in expected.items():
        body=client.get('/api/municipal/pincodes/'+city).json()
        assert body['coverage']==count and body['complete'] is False
        assert all(isinstance(r['pincode'],str) and len(r['pincode'])==6 and r['latitude'] is None for r in body['records'])
    with connection() as db:
        assert db.execute('SELECT count(*) n FROM schema_migrations').fetchone()['n']==1
        assert db.execute('SELECT pincode FROM complaint_jurisdictions WHERE complaint_id=?',(existing['id'],)).fetchone()['pincode']=='110001'
    assert client.get('/api/municipal/local/chennai?pincode=110001').status_code==422


def test_database_password_hash_and_scoped_session(client):
    p=officer(client)
    with connection() as db:
        row=db.execute('SELECT * FROM admin_users WHERE id=?',(p['id'],)).fetchone()
        assert row['password_hash'].startswith('scrypt$') and verify_password('Test-password-2026',row['password_hash'])
        assert 'Test-password-2026' not in row['password_hash']
    me=client.get('/api/auth/me').json()
    assert me['profile']['assignments'][0]['pincode']=='110001'
    assert 'password_hash' not in json.dumps(me)
    with pytest.raises(ValueError):provision('pin-password','110001','Invalid password user','officer',['110001'])
    assert client.get('/api/audit').status_code==403
    assert client.get('/api/municipal/administrators').status_code==403


def test_report_routes_to_assigned_officer_and_retries_do_not_duplicate(client):
    p=officer(client)
    first=report(client,people=500);second=report(client,people=500)
    assert first.status_code==201 and second.status_code==201
    assert first.json()['id']==second.json()['id']
    stored=repo.get('complaint',first.json()['id'])
    assert stored['assigned_admin_id']==p['id'] and stored['reported_affected_people_count']==500
    assert stored['affected_people_count'] is None and stored['damage_priority'] is None
    assert 'email_private' not in first.json()
    assert len(repo.all_records('complaint'))==1


def test_cross_pin_review_and_parameter_tampering_rejected(client):
    own=report(client).json();other=report(client,'110002','Another locality incident').json()
    officer(client)
    queue=client.get('/api/civic/review?city_id=delhi').json()
    assert {r['id'] for r in queue}=={own['id']}
    assert review(client,other['id']).status_code==403
    assert client.post('/api/complaints/'+other['id'],json={'status':'under_review','note':'Tampered request'}).status_code==403
    assert client.get('/api/civic/review?city_id=chennai').status_code==403
    assert client.post('/api/scenarios',json={**client.get('/api/scenarios/defaults').json(),'pincode':'110002'}).status_code==403
    assert client.get('/api/resources/pools?city_id=chandigarh').status_code==403


def test_scoped_notices_active_visibility_and_expired_archive(client):
    officer(client)
    now=datetime.now(timezone.utc)
    def payload(pin,start,end):return {'city_id':'delhi','pincode':pin,'headline':'Local water works','area':'Listed locality','description':'Water works will affect this locality.','valid_from':start.isoformat(),'valid_until':end.isoformat()}
    active=payload('110001',now-timedelta(hours=1),now+timedelta(hours=1))
    response=client.post('/api/civic/notices',json=active);assert response.status_code==201
    assert response.json()['publisher']=='CivicFlux officer'
    assert client.post('/api/civic/notices',json={**active,'pincode':'110002'}).status_code==403
    assert len(client.get('/api/municipal/local/delhi?pincode=110001').json()['notices'])>=1
    assert not any(n['id']==response.json()['id'] for n in client.get('/api/municipal/local/delhi?pincode=110002').json()['notices'])
    expired=client.post('/api/civic/notices',json=payload('110001',now-timedelta(hours=3),now-timedelta(hours=2))).json()
    assert not any(n['id']==expired['id'] for n in client.get('/api/municipal/local/delhi?pincode=110001').json()['notices'])
    assert any(n['id']==expired['id'] for n in client.get('/api/municipal/notice-archive/delhi?pincode=110001').json())


def test_location_lookup_unavailable_does_not_block_manual_pins(client):
    result=client.post('/api/municipal/locate/delhi',json={'latitude':28.6,'longitude':77.2})
    assert result.status_code==200 and result.json()['status']=='manual_selection_required' and result.json()['pincode'] is None
    assert client.get('/api/municipal/pincodes/delhi').status_code==200


def test_locality_plan_approval_reserves_once_and_persists(admin_client):
    c=admin_client;r=report(c).json();assert review(c,r['id']).status_code==200
    inventory=pool(c);budget=funding(c,inventory)
    response=c.post('/api/locality-planning/plans',json={'budget_id':budget['id']});assert response.status_code==201,response.text
    p=response.json();selected=p['allocation']['comparisons']['CP-SAT']['selected']
    assert len(selected)==1 and selected[0]['case_id']==r['id']
    body={'decision':'approve_internal','note':'Reviewed complete response package','pool_id':inventory['id'],'assignments':{r['id']:{'crews':1,'workers':2,'vehicles':1}}}
    approved=c.post('/api/locality-planning/plans/'+p['id']+'/decision',json=body)
    assert approved.status_code==200,approved.text
    again=c.post('/api/locality-planning/plans/'+p['id']+'/decision',json=body)
    assert again.status_code==200 and again.json()['already_approved']
    saved=c.get('/api/locality-planning/plans?city_id=delhi').json()
    assert saved[0]['reservation']['requirements']['budget']==5000 and saved[0]['external_dispatch'] is False
    repo.initialize()
    assert c.get('/api/locality-planning/plans?city_id=delhi').json()[0]['internal_review_status']=='approve_internal'
    # Confirm the saved approval survives a fresh interpreter and application startup.
    import os,subprocess,sys
    from backend import config
    from project_paths import PROJECT_ROOT
    environment=os.environ.copy()
    environment.update(CIVICFLUX_DB=str(config.DB_PATH),CIVICFLUX_ROOT=str(PROJECT_ROOT),CIVICFLUX_PUBLIC_FEEDS='0',CIVICFLUX_ADMIN_ID='admin',CIVICFLUX_ADMIN_PASSWORD='001',CIVICFLUX_TEST_PLAN_ID=p['id'])
    script="""import os
from fastapi.testclient import TestClient
from backend.main import app
with TestClient(app) as client:
    assert client.post('/api/auth/login',json={'username':'admin','password':'001'}).status_code==200
    plans=client.get('/api/locality-planning/plans?city_id=delhi').json()
    saved=next(p for p in plans if p['id']==os.environ['CIVICFLUX_TEST_PLAN_ID'])
    assert saved['internal_review_status']=='approve_internal'
    assert saved['reservation']['requirements']['budget']==5000
"""
    restarted=subprocess.run([sys.executable,'-c',script],cwd=PROJECT_ROOT,env=environment,capture_output=True,text=True,timeout=30)
    assert restarted.returncode==0,restarted.stderr

    assert c.get('/api/resources/pools?city_id=delhi').json()[0]['available']['budget']==95000
    assert c.post('/api/locality-planning/plans/'+p['id']+'/decision',json={**body,'decision':'release'}).status_code==200
    assert c.get('/api/resources/pools?city_id=delhi').json()[0]['available']['budget']==100000


def test_approval_rejects_missing_or_understated_packages(admin_client):
    c=admin_client;r=report(c).json();review(c,r['id']);inventory=pool(c);budget=funding(c,inventory)
    p=c.post('/api/locality-planning/plans',json={'budget_id':budget['id']}).json()
    endpoint='/api/locality-planning/plans/'+p['id']+'/decision'
    body={'decision':'approve_internal','note':'Needs package validation','pool_id':inventory['id'],'assignments':{}}
    assert c.post(endpoint,json=body).status_code==422
    assert c.post(endpoint,json={**body,'assignments':{r['id']:{'crews':1,'workers':1,'vehicles':0}}}).status_code==422
    assert c.get('/api/resources/pools?city_id=delhi').json()[0]['available']['budget']==100000


def test_funding_cannot_exceed_pool_and_wrong_pin_is_forbidden(client):
    officer(client);p=pool(client)
    body={'city_id':'delhi','pincode':'110001','pool_id':p['id'],'budget':100001,'fiscal_year':'2026–27','source_ref':'Test allocation'}
    assert client.post('/api/locality-planning/budgets',json=body).status_code==409
    assert client.post('/api/locality-planning/budgets',json={**body,'pincode':'110002','budget':1}).status_code==403


def test_priority_weights_missing_population_and_capacity_constraints():
    base={'case_id':'a','cost':100,'crew_type':'drain','duration_hours':1,'pumps_required':0,'required_crews':1,'required_workers':2,'required_vehicles':1,'damage_priority':'Critical','severity':4,'affected_people_count':100,'population_basis':'estimated'}
    capacity={'budget':100,'pumps':0,'crews':1,'workers':2,'vehicles':1,'crew_hours':{'drain':1,'water':0,'road':0}}
    result=plan_localities([base,{**base,'case_id':'b','affected_people_count':None}],capacity)
    assert result['candidates'][0]['priority_score']==pytest.approx(1)
    assert result['candidates'][1]['normalized_population'] is None
    assert 'unknown' in result['candidates'][1]['reason']
    for plan in result['comparisons'].values():
        assert plan['used']['budget']<=100 and plan['used']['workers']<=2 and plan['used']['vehicles']<=1


def test_cross_origin_login_and_password_bruteforce_are_rejected(client):
    assert client.post('/api/auth/login',json={'username':'admin','password':'bad'},headers={'Origin':'https://untrusted.example'}).status_code==403
    for _ in range(8):assert client.post('/api/auth/login',json={'username':'missing-officer','password':'wrong-password'}).status_code==401
    assert client.post('/api/auth/login',json={'username':'missing-officer','password':'wrong-password'}).status_code==429


def test_stale_assessment_cannot_be_approved_and_incident_cannot_be_reserved_twice(admin_client):
    c=admin_client;r=report(c).json();review(c,r['id']);inventory=pool(c);budget=funding(c,inventory)
    create=lambda:c.post('/api/locality-planning/plans',json={'budget_id':budget['id']}).json()
    stale=create();review(c,r['id'],population=150)
    body={'decision':'approve_internal','note':'Review complete and eligible','pool_id':inventory['id'],'assignments':{r['id']:{'crews':1,'workers':2,'vehicles':1}}}
    assert c.post('/api/locality-planning/plans/'+stale['id']+'/decision',json=body).status_code==409
    a,b=create(),create()
    assert c.post('/api/locality-planning/plans/'+a['id']+'/decision',json=body).status_code==200
    assert c.post('/api/locality-planning/plans/'+b['id']+'/decision',json=body).status_code==409
    with connection() as db:assert db.execute("SELECT count(*) n FROM resource_reservations WHERE status='reserved'").fetchone()['n']==1


def test_budget_and_report_city_pin_database_constraints(client):
    import sqlite3
    item=repo.append('complaint',{'city_id':'chennai','status':'submitted'})
    with pytest.raises(sqlite3.IntegrityError):
        with connection() as db:db.execute('INSERT INTO complaint_jurisdictions VALUES (?,?,?,NULL)',(item['id'],'110001','chennai'))


def test_revoked_officer_session_cannot_keep_old_assignments(client):
    officer(client)
    provision('pin-officer','Replacement-password-2026','Reassigned officer','officer',['110002'])
    assert client.get('/api/auth/me').status_code==401


def test_geocoder_only_suggests_registered_pin_and_keeps_manual_confirmation(client,monkeypatch):
    import backend.api.municipal as module
    monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','1');monkeypatch.setattr(module,'_geo_cache',{});monkeypatch.setattr(module,'_geo_clock',0)
    calls=[]
    class Result:
        def raise_for_status(self):pass
        def json(self):return {'address':{'postcode':'110001','suburb':'Reference locality'}}
    class HTTP:
        def __init__(self,**kwargs):assert 'CivicFlux' in kwargs['headers']['User-Agent']
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def get(self,url,params):calls.append(params);return Result()
    monkeypatch.setattr(module.httpx,'AsyncClient',HTTP)
    body={'latitude':28.61234,'longitude':77.21234}
    response=client.post('/api/municipal/locate/delhi',json=body)
    assert response.status_code==200 and response.json()['status']=='suggestion'
    assert response.json()['pincode']=='110001' and 'Confirm' in response.json()['note']
    assert client.post('/api/municipal/locate/delhi',json=body).status_code==200 and len(calls)==1
    assert client.post('/api/municipal/locate/delhi',json={'latitude':900,'longitude':77}).status_code==422


def test_forecast_optional_fields_preserve_units_and_missing_values():
    from backend.services.outlook_service import parse
    from backend.services.city_service import city
    today=datetime(2026,10,28).date()
    payload={'latitude':28.6,'longitude':77.2,'timezone':'Asia/Kolkata','daily_units':{'temperature_2m_max':'°C','temperature_2m_min':'°C','precipitation_sum':'mm','wind_speed_10m_max':'km/h','weather_code':'wmo code','precipitation_probability_max':'%'},'daily':{'time':['2026-10-29'],'temperature_2m_max':[30],'temperature_2m_min':[20],'precipitation_sum':[5],'wind_speed_10m_max':[12],'weather_code':[61],'precipitation_probability_max':[70]},'hourly_units':{'apparent_temperature':'°C','relative_humidity_2m':'%'},'hourly':{'time':['2026-10-29T12:00','2026-10-29T13:00'],'apparent_temperature':[31,33],'relative_humidity_2m':[60,80]}}
    row=parse(payload,city('delhi'),today)[0]
    assert row['precipitation_probability_max']==70 and row['apparent_temperature_mean']==32 and row['relative_humidity_2m_mean']==70
    payload['daily']['precipitation_probability_max']=[999]
    assert parse(payload,city('delhi'),today)[0]['precipitation_probability_max'] is None


def test_locality_summary_distinguishes_report_claims_and_officer_estimates(admin_client):
    r=report(admin_client,people=500).json()
    review(admin_client,r['id'],population=100)
    rows=admin_client.get('/api/locality-planning/summary?city_id=delhi').json()['rows']
    row=next(r for r in rows if r['pincode']=='110001')
    assert row['reported_problems']==1 and row['verified_reports']==1
    assert row['assessed_population_estimates_sum']==100
    assert row['severity_distribution']['Critical']==1 and row['declared_locality_budget']==0


def test_population_verification_needs_evidence_and_old_reviews_preserve_assessments(admin_client):
    r=report(admin_client).json();review(admin_client,r['id'],population=100)
    bad={'validation':'valid','status':'under_review','department':'Drainage','damage_priority':'High','affected_people_count':100,'population_basis':'verified'}
    assert admin_client.post('/api/civic/review/'+r['id'],json=bad).status_code==422
    # Existing status/reply API clients do not overwrite newly assessed packages by omission.
    assert admin_client.post('/api/civic/review/'+r['id'],json={'validation':'valid','status':'under_review','department':'Drainage'}).status_code==200
    saved=repo.get('complaint',r['id'])
    assert saved['affected_people_count']==100 and saved['intervention_cost']==5000
    assert saved['required_workers']==2 and saved['damage_priority']=='Critical'


def test_legacy_report_can_gain_a_validated_pin_without_losing_history(admin_client):
    old=repo.append('complaint',{'city_id':'delhi','title':'Legacy retained issue','description':'An existing imported issue','location':'Recorded place','category':'drainage','status':'submitted','history':[{'note':'Original retained history'}]})
    result=admin_client.post('/api/civic/review/'+old['id'],json={'postal_code':'110001','validation':'needs_information','status':'under_review','department':'Drainage'})
    assert result.status_code==200,result.text
    saved=repo.get('complaint',old['id']);assert saved['postal_code']=='110001' and saved['history'][0]['note']=='Original retained history'
    with connection() as db:assert db.execute('SELECT pincode FROM complaint_jurisdictions WHERE complaint_id=?',(old['id'],)).fetchone()['pincode']=='110001'


def test_locality_optimizer_counts_crew_hours_and_work_window():
    case={'case_id':'crew-package','cost':100,'crew_type':'drain','duration_hours':2,'pumps_required':0,'required_crews':2,'required_workers':2,'required_vehicles':0,'damage_priority':'High','severity':3,'affected_people_count':None,'population_basis':'unknown'}
    capacity={'budget':1000,'pumps':0,'crews':2,'workers':2,'vehicles':0,'crew_hours':{'drain':3,'road':0,'water':0},'work_window_hours':8}
    result=plan_localities([case],capacity)
    assert all(not p['selected'] for p in result['comparisons'].values())
    capacity['crew_hours']['drain']=4
    assert plan_localities([case],capacity)['comparisons']['CP-SAT']['used']['crew_hours']['drain']==4
    capacity['work_window_hours']=1
    assert not plan_localities([case],capacity)['comparisons']['CP-SAT']['selected']


def test_explanation_uses_saved_global_evidence_without_inventing_local_shap(client):
    from pathlib import Path
    import hashlib
    from project_paths import PROJECT_ROOT
    for component in ('rainfall','aqi','traffic','flood','water_network','cascade_risk'):
        response=client.get('/api/assessments/'+component+'/explanation')
        assert response.status_code==200
        body=response.json();assert body['status']=='available' and body['features'] and body['local_attribution_available'] is False
        assert hashlib.sha256((PROJECT_ROOT/body['source']).read_bytes()).hexdigest()==body['source_sha256']
        assert all(isinstance(r['importance'],float) for r in body['features'])
    # Success-classifier importance is not an explanation of the duration model.
    result=client.get('/api/assessments/intervention_outcomes/explanation').json()
    assert result['status']=='unavailable' and result['features']==[]


def test_alternative_approval_tracks_actual_incidents_and_blocks_duplicate_packages(admin_client):
    c=admin_client;a=report(c,title='Critical small population').json();b=report(c,title='Medium large population').json()
    review(c,a['id'],population=100);review(c,b['id'],population=1000)
    changed=c.post('/api/civic/review/'+b['id'],json={'validation':'valid','status':'under_review','department':'Drainage','damage_priority':'Medium'})
    assert changed.status_code==200
    inventory=pool(c);budgets=[]
    for _ in range(2):
        response=c.post('/api/locality-planning/budgets',json={'city_id':'delhi','pincode':'110001','pool_id':inventory['id'],'budget':5000,'fiscal_year':'2026–27','source_ref':'Distinct test funding allocation'})
        assert response.status_code==201;budgets.append(response.json())
    plans=[c.post('/api/locality-planning/plans',json={'budget_id':budget['id']}).json() for budget in budgets]
    assert plans[0]['allocation']['comparisons']['CP-SAT']['selected'][0]['case_id']==b['id']
    assert plans[0]['allocation']['comparisons']['severity_greedy']['selected'][0]['case_id']==a['id']
    decision={'decision':'approve_internal','note':'Reviewed severity-first alternative','method':'severity_greedy','pool_id':inventory['id'],'assignments':{a['id']:{'crews':1,'workers':2,'vehicles':1}}}
    assert c.post('/api/locality-planning/plans/'+plans[0]['id']+'/decision',json=decision).status_code==200
    assert c.post('/api/locality-planning/plans/'+plans[1]['id']+'/decision',json=decision).status_code==409
    saved=next(p for p in c.get('/api/locality-planning/plans?city_id=delhi').json() if p['id']==plans[0]['id'])
    assert saved['incident_ids']==[a['id']]


def test_legacy_unattributed_notices_are_retained_but_not_presented_as_verified_alerts(client):
    now=datetime.now(timezone.utc)
    legacy=repo.append('civic_notice',{'city_id':'delhi','kind':'platform_notice','headline':'Legacy unverified placeholder','area':'Recorded locality','description':'Requires authenticated review before public alerting.','publisher':'CivicFlux officer','valid_from':(now-timedelta(hours=1)).isoformat(),'valid_until':(now+timedelta(hours=1)).isoformat()})
    assert repo.get('civic_notice',legacy['id'])['headline']=='Legacy unverified placeholder'
    notices=client.get('/api/municipal/local/delhi').json()['notices']
    assert not any(n['id']==legacy['id'] for n in notices)
