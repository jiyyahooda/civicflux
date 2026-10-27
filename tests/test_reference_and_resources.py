from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
from io import StringIO
from pathlib import Path
import hashlib
import pandas as pd
import pytest
from fastapi import HTTPException
from backend import config
from backend.api.resources import Decision,decide
from project_paths import PROJECT_ROOT
from src.civicflux.integration import fixture

def test_reference_tables_retain_scope_dates_and_reconciliation(client):
 ref=client.get('/api/reference/delhi').json()
 assert len(ref['budget'])==16 and len(ref['drainage_basins'])==3 and len(ref['roads'])==29
 assert not ref['operational_eligible']
 totals={x['fiscal_year']:x for x in ref['budget_totals']}
 assert totals['2025-26']['reported_total_crore']==17011.92
 assert totals['2025-26']['listed_groups_crore']==16131.02
 assert totals['2025-26']['unreconciled_difference_crore']==880.9
 assert totals['2024-25']['unreconciled_difference_crore']==233.18
 assert sum(b['historical_natural_drains'] for b in ref['drainage_basins'])==201
 assert all(b['inventory_year']==1976 and b['geometry'] is None for b in ref['drainage_basins'])
 assert next(x['value'] for x in ref['transport'] if x['id']=='registered_vehicles')==8761919
 assert client.get('/api/reference/chennai').json()['status']=='unavailable'
 assert client.get('/api/reference/chandigarh').json()['status']=='unavailable'
 assert client.get('/api/civic/context/delhi').json()['operational_pools']==[]
 doc=client.get('/api/reference/delhi/source');assert doc.status_code==200 and doc.content.startswith(b'%PDF')
 assert hashlib.sha256(doc.content).hexdigest()==ref['source_sha256']

def scenario(client):
 defaults=client.get('/api/scenarios/defaults').json()
 result=client.post('/api/scenarios',json=defaults)
 assert result.status_code==200,result.text
 return result.json()

def pool_for(client,plan):
 p=plan['allocation']['comparisons']['CP-SAT'];n=len(p['selected']);now=datetime.now(timezone.utc)
 body={'city_id':'delhi','department':'Drainage test department','service_area':'Declared test area','specialization':'Mixed water road drain','workers_on_shift':n+5,'workers':n,'crews':n,'pumps':p['used']['pumps'],'vehicles':0,'equipment':'Test roster only','budget':p['used']['budget'],'crew_hours':p['used']['crew_hours'],'source_ref':'Authorized disposable test roster','valid_from':(now-timedelta(hours=1)).isoformat(),'valid_until':(now+timedelta(days=1)).isoformat()}
 result=client.post('/api/resources/pools',json=body);assert result.status_code==201,result.text
 return result.json(),body

def approval(plan,pool):
 return {'decision':'approve_internal','note':'Supervised internal what-if reservation','method':'CP-SAT','pool_id':pool['id'],'assignments':{c['case_id']:{'crews':1,'workers':1,'vehicles':0} for c in plan['allocation']['comparisons']['CP-SAT']['selected']}}

def test_resource_endpoints_are_protected(client):
 assert client.get('/api/resources/pools?city_id=delhi').status_code==401
 assert client.post('/api/resources/pools',json={}).status_code==401
 assert client.get('/api/resources/plans/unknown').status_code==401
 assert client.post('/api/resources/plans/unknown/decision',json={}).status_code==401

def test_internal_approval_reserves_and_release_restores_capacity(admin_client):
 plan=scenario(admin_client);pool,body=pool_for(admin_client,plan);request=approval(plan,pool)
 result=admin_client.post('/api/resources/plans/'+plan['id']+'/decision',json=request)
 assert result.status_code==200,result.text
 assert result.json()['reservation']['external_dispatch'] is False
 pools=admin_client.get('/api/resources/pools?city_id=delhi').json();assert pools[0]['available']['budget']==0
 assert pools[0]['available']['crews']==0 and pools[0]['assigned']['crews']==pool['crews']
 # An identical retry is idempotent: same reservation and no extra approval history.
 retry=admin_client.post('/api/resources/plans/'+plan['id']+'/decision',json=request)
 assert retry.status_code==200 and retry.json()['already_approved'] is True
 assert retry.json()['reservation']['id']==result.json()['reservation']['id']
 pools=admin_client.get('/api/resources/pools?city_id=delhi').json();assert pools[0]['assigned']['budget']==pool['budget']
 reduced={**body,'budget':0}
 assert admin_client.post('/api/resources/pools/'+pool['id'],json=reduced).status_code==409
 assert admin_client.post('/api/feedback/'+plan['id']+'/review',json={'decision':'approve','note':'Scientific approval is separate'}).status_code==409
 release=admin_client.post('/api/resources/plans/'+plan['id']+'/decision',json={'decision':'release','note':'Release completed planning reservation'})
 assert release.status_code==200
 assert admin_client.get('/api/resources/pools?city_id=delhi').json()[0]['available']['budget']==pool['budget']
 history=admin_client.get('/api/resources/plans/'+plan['id']).json();assert len(history['history'])==2 and history['reservation'] is None
 assert any(a['event']=='internal_plan_approve_internal' for a in admin_client.get('/api/audit').json())

def test_concurrent_plans_cannot_double_book_inventory(admin_client):
 a=scenario(admin_client);b=scenario(admin_client);pool,_=pool_for(admin_client,a)
 def attempt(plan):
  try:decide(plan['id'],Decision(**approval(plan,pool)),config.ADMIN_ID);return 200
  except HTTPException as error:return error.status_code
 with ThreadPoolExecutor(max_workers=2) as executor:codes=list(executor.map(attempt,[a,b]))
 assert sorted(codes)==[200,409]
 current=admin_client.get('/api/resources/pools?city_id=delhi').json()[0]
 assert current['assigned']['budget']==pool['budget'] and current['available']['budget']==0

def test_inventory_city_and_shift_validity_are_enforced(admin_client):
 plan=scenario(admin_client);pool,body=pool_for(admin_client,plan)
 assert admin_client.post('/api/resources/pools',json=body).status_code==409
 other={**body,'city_id':'chennai'};foreign=admin_client.post('/api/resources/pools',json=other).json()
 assert admin_client.post('/api/resources/plans/'+plan['id']+'/decision',json=approval(plan,foreign)).status_code==409
 past={**body,'valid_from':(datetime.now(timezone.utc)-timedelta(days=2)).isoformat(),'valid_until':(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()}
 assert admin_client.post('/api/resources/pools/'+pool['id'],json=past).status_code==200
 assert admin_client.post('/api/resources/plans/'+plan['id']+'/decision',json=approval(plan,pool)).status_code==409

def test_custom_water_histories_and_anomaly_sensor_use_original_serving(client):
 catalog=client.get('/api/assessments?city_id=delhi').json()
 anomaly=next(x for x in catalog if x['id']=='infrastructure_anomaly')
 sensors=next(f['options'] for f in anomaly['fields'] if f['key']=='sensor')
 assert 'rainfall:Delhi' in sensors and 'aqi:Delhi' in sensors
 response=client.post('/api/assessments/infrastructure_anomaly',json={'city_id':'delhi','values':{'sensor':'aqi:Delhi'}})
 assert response.status_code==200 and response.json()['status']=='complete',response.text
 f=fixture('water_network',PROJECT_ROOT)
 csvs={k:pd.DataFrame(rows).to_csv(index=False) for k,rows in f['measurements'].items()}
 body={'city_id':'delhi','mode':'custom','measurement_csv':csvs,'as_of':f['as_of'],'observation_time':f['observation_time'],'units_confirmed':True}
 result=client.post('/api/assessments/water_network',json=body)
 assert result.status_code==200 and result.json()['status']=='complete',result.text
 assert result.json()['local_prediction'] is False
 body['units_confirmed']=False
 assert client.post('/api/assessments/water_network',json=body).status_code==422
