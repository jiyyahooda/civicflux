from datetime import datetime,timezone,timedelta
from io import BytesIO
import json
from PIL import Image
import pytest
from backend import config
from backend.services.civic_service import postal
from src.civicflux.serving import discover
from project_paths import PROJECT_ROOT

def image_bytes():
    stream=BytesIO();Image.new('RGB',(20,20),(30,60,90)).save(stream,format='JPEG');return stream.getvalue()

def report(client,**changes):
    body={'city_id':'delhi','title':'Blocked drain','category':'drainage','location':'Recorded test locality','description':'Drain blockage awaiting officer inspection.','postal_code':'110001','email':'citizen@example.org','latitude':'28.65','longitude':'77.23',**changes}
    return client.post('/api/civic/reports',data=body,files=[('images',('unsafe-name.jpg',image_bytes(),'image/jpeg'))])

def login(client):
    assert client.post('/api/auth/login',json={'username':config.ADMIN_ID,'password':config.ADMIN_PASSWORD}).status_code==200

def test_report_requires_real_image_city_pin_email_and_persists_privately(client):
    data={'city_id':'delhi','title':'Street issue','category':'road','location':'Test street','description':'A surface issue was reported.','postal_code':'110001','email':'citizen@example.org'}
    assert client.post('/api/civic/reports',data=data).status_code==422
    assert client.post('/api/civic/reports',data=data,files={'images':('fake.jpg',b'not a photo','image/jpeg')}).status_code==422
    assert report(client,email='invalid').status_code==422
    assert report(client,postal_code='600001').status_code==422
    response=report(client);assert response.status_code==201,response.text
    item=response.json();assert 'email_private' not in item and 'internal_notes' not in item
    stored=client.get('/api/civic/reports?city_id=delhi').json();assert stored[0]['id']==item['id']
    assert client.get('/api/civic/reports?city_id=chennai').json()==[]
    photo=client.get(item['images'][0]['url']);assert photo.status_code==200 and photo.headers['content-type']=='image/jpeg'
    assert client.get('/api/civic/review?city_id=delhi').status_code==401
    assert client.get('/api/civic/planning/delhi').status_code==401
    assert client.get('/api/scenarios').status_code==401
    assert client.get('/api/feedback').status_code==401
    assert client.post('/api/complaints',json={'city_id':'delhi','category':'road','location':'Test street','description':'Legacy public bypass attempt'}).status_code==401

def test_review_private_notes_public_reply_and_verified_location(client):
    item=report(client).json();login(client)
    assert client.get('/api/civic/review?city_id=delhi').json()[0]['email_private']=='citizen@example.org'
    body={'validation':'valid','status':'under_review','department':'Drainage','public_reply':'An inspection is being arranged.','internal_notes':'Private assignment note','coordinates_verified':True}
    result=client.post('/api/civic/review/'+item['id'],json=body);assert result.status_code==200,result.text
    public=client.get('/api/civic/reports?city_id=delhi').json()[0]
    assert public['coordinates_verified'] and public['public_reply']==body['public_reply']
    assert 'Private assignment note' not in json.dumps(public)
    assert 'citizen@example.org' not in client.get('/api/complaints').text
    body['status']='closed';assert client.post('/api/civic/review/'+item['id'],json=body).status_code==422
    body['completion_evidence']='Verified field completion record';assert client.post('/api/civic/review/'+item['id'],json=body).status_code==200
    assert client.get('/api/civic/planning/delhi').json()['message']=='No confirmed active issues in the available records.'
    assert any(x['event']=='officer_report_review' for x in client.get('/api/audit').json())

def test_notices_expire_and_rosters_are_city_scoped(client):
    login(client);now=datetime.now(timezone.utc)
    body={'city_id':'chennai','valid_from':(now-timedelta(hours=1)).isoformat(),'valid_until':(now+timedelta(hours=1)).isoformat(),'headline':'Officer test notice','area':'Recorded test area','description':'Check the current officer information.','kind':'platform_notice'}
    assert client.post('/api/civic/notices',json=body).status_code==201
    body['valid_from']=(now-timedelta(days=2)).isoformat();body['valid_until']=(now-timedelta(days=1)).isoformat()
    assert client.post('/api/civic/notices',json=body).status_code==201
    assert len(client.get('/api/civic/context/chennai').json()['notices'])==1
    assert not any(n['headline']=='Officer test notice' for n in client.get('/api/civic/context/delhi').json()['notices'])
    body.update(kind='official_import',source_url='https://traffic.delhipolice.gov.in/en')
    assert client.post('/api/civic/notices',json=body).status_code==422
    inventory={'city_id':'chennai','valid_from':(now-timedelta(minutes=1)).isoformat(),'valid_until':(now+timedelta(hours=1)).isoformat(),'budget':1000,'crew_hours':10,'pumps':1,'vehicles':1,'source_ref':'Authorized test roster','scope':'Test area'}
    assert client.post('/api/civic/inventory',json=inventory).status_code==201
    assert len(client.get('/api/civic/context/chennai').json()['inventory'])==1
    assert not client.get('/api/civic/context/delhi').json()['inventory']

def test_all_nine_assessment_adapters_call_saved_systems_and_abstain(client):
    catalog=client.get('/api/assessments?city_id=chennai').json();assert len(catalog)==9
    assert all(not tool['city_prediction_available'] for tool in catalog)
    for entry in discover(PROJECT_ROOT):
        component=entry['component']
        response=client.post('/api/assessments/'+component,json={'city_id':'chennai','mode':'reference','values':{}})
        assert response.status_code==200,(component,response.text)
        result=response.json();assert result['status']=='complete',(component,result)
        assert result['metrics'] and not result['local_prediction']
        assert 'confidence' not in result
        local=client.post('/api/assessments/'+component,json={'city_id':'chennai','mode':'city','values':{}}).json()
        assert local['status']=='unavailable' and local['metrics']==[]
    invalid=client.post('/api/assessments/flood',json={'city_id':'delhi','values':{'area_m2':5}})
    assert invalid.status_code==422

def test_postal_catalog_uses_exact_records_and_flags_limited_coverage(client):
    assert postal('chennai')['source_url'].startswith('https://chennai.nic.in/')
    assert len(postal('delhi')['records'])>100
    assert report(client,city_id='chandigarh',postal_code='160017',latitude='30.73',longitude='76.78').status_code==201
    assert report(client,city_id='chandigarh',postal_code='160999',latitude='30.73',longitude='76.78').status_code==422

def test_weather_fails_closed_and_never_reuses_another_city(client):
    for identifier in ['delhi','chennai','chandigarh']:
        result=client.get('/api/civic/weather/'+identifier).json()
        assert result['city_id']==identifier and result['status']=='unavailable'
        assert result['current'] is None and result['days']==[]
    assert client.get('/api/civic/weather/unknown').status_code==404

def test_resource_proposals_require_current_roster_and_respect_capacity(client):
    item=report(client).json();login(client)
    review={'validation':'valid','status':'under_review','department':'Drainage','proposed_budget':100,'proposed_crew_hours':1,'proposed_pumps':1}
    assert client.post('/api/civic/review/'+item['id'],json=review).status_code==409
    now=datetime.now(timezone.utc)
    roster={'city_id':'delhi','valid_from':(now-timedelta(minutes=1)).isoformat(),'valid_until':(now+timedelta(hours=1)).isoformat(),'budget':100,'crew_hours':1,'pumps':1,'vehicles':0,'source_ref':'Authorized disposable test roster','scope':'Test area'}
    assert client.post('/api/civic/inventory',json=roster).status_code==201
    review['proposed_pumps']=2
    assert client.post('/api/civic/review/'+item['id'],json=review).status_code==422
    review['proposed_pumps']=1
    assert client.post('/api/civic/review/'+item['id'],json=review).status_code==200
