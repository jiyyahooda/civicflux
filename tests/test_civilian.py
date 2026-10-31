import json,time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.api import civilian as c
from backend.db.connection import connection
from backend.db import repository as repo
from civilian_helpers import sign_in,SENT
from test_civic_workflows import image_bytes

real_sms_transport=c.sms_send

def payload():return {'city_id':'delhi','title':'Camera evidence','category':'road','location':'Test locality','description':'An issue photographed for review.','postal_code':'110001','email':'private@example.org'}
def send(client,phone='9000000001'):
 r=client.post('/api/civilian/otp/send',json={'phone':phone,'name':'Test Citizen'});assert r.status_code==200,r.text;return r.json()['challenge_id']
def verify(client,id,code='123456'):return client.post('/api/civilian/otp/verify',json={'challenge_id':id,'otp':code})
def test_guest_can_report_without_reading_registered_private_profiles(client):
 assert client.get('/api/civilian/session').json()['user'] is None
 for path in ['/api/civilian/reports','/api/civilian/saved']:assert client.get(path).status_code==401
 r=client.post('/api/civic/reports',data=payload(),files={'images':('camera.jpg',image_bytes(),'image/jpeg')})
 assert r.status_code==201,r.text
 assert repo.get('complaint',r.json()['id'])['civilian_id'] is None
 route=client.post('/api/civilian/travel/check',json={'city_id':'delhi','path':[{'latitude':28.6,'longitude':77.2,'label':'A'},{'latitude':28.7,'longitude':77.3,'label':'B'}]})
 assert route.status_code==200
 assert client.get('/api/civilian/saved').status_code==401
def test_otp_is_hashed_bound_and_single_use(client):
 id=send(client);code=SENT['9000000001']
 with connection() as db:
  row=db.execute('SELECT * FROM civilian_otp WHERE id=?',(id,)).fetchone();assert row['code_hash']!=code
 other=TestClient(app)
 assert verify(other,id,code).status_code==400
 r=verify(client,id,code);assert r.status_code==200,r.text
 assert 'httponly' in r.headers['set-cookie'].lower() and 'samesite=strict' in r.headers['set-cookie'].lower()
 assert verify(client,id,code).status_code==400
 assert client.get('/api/civilian/session').json()['user']['phone']=='9000000001'
 assert client.get('/api/civilian/session').headers['cache-control']=='no-store'
def test_wrong_attempts_persist_and_expired_codes_fail(client):
 id=send(client);code=SENT['9000000001'];wrong='000000' if code!='000000' else '111111'
 for _ in range(5):assert verify(client,id,wrong).status_code==400
 assert verify(client,id,code).status_code==400
 with connection() as db:assert db.execute('SELECT attempts FROM civilian_otp WHERE id=?',(id,)).fetchone()[0]==5
 id=send(client,'9000000002')
 with connection() as db:db.execute('UPDATE civilian_otp SET expires=? WHERE id=?',(time.time()-1,id))
 assert verify(client,id,SENT['9000000002']).status_code==400
 assert client.get('/api/civilian/session').json()['user'] is None
def test_resend_throttled_and_no_secrets_returned(client):
 first=client.post('/api/civilian/otp/send',json={'name':'Test Citizen','phone':'9000000001'})
 assert first.status_code==200
 assert not any(k in first.json() for k in ('otp','key','phone','code'))
 assert client.post('/api/civilian/otp/send',json={'name':'Test Citizen','phone':'9000000001'}).status_code==429
 assert client.post('/api/civilian/otp/send',json={'name':'Test Citizen','phone':'123'}).status_code==422
 assert client.post('/api/civilian/otp/send',json={'name':'  ','phone':'9000000002'}).status_code==422
 assert client.post('/api/civilian/otp/send',headers={'Origin':'https://evil.example'},json={'name':'Test Citizen','phone':'9000000002'}).status_code==403

def test_provider_failure_and_missing_config_do_not_login(client,monkeypatch):
 async def fail(*args):raise c.HTTPException(503,'Provider unavailable')
 monkeypatch.setattr(c,'sms_send',fail)
 assert client.post('/api/civilian/otp/send',json={'name':'Test Citizen','phone':'9000000001'}).status_code==503
 assert client.get('/api/civilian/session').json()['user'] is None
 monkeypatch.delenv('FAST2SMS_OTP_TEMPLATE_ID')
 assert client.post('/api/civilian/otp/send',json={'name':'Test Citizen','phone':'9000000002'}).status_code==503
 assert not client.get('/api/civilian/session').json()['sms_configured']

def test_owner_only_profiles_places_reports_and_logout(client):
 first=sign_in(client)
 body={'kind':'place','label':'Home','points':[{'latitude':28.6,'longitude':77.2,'label':'Private address'}]}
 s=client.post('/api/civilian/saved',json=body);assert s.status_code==201,s.text
 assert client.post('/api/civilian/profile',json={'name':'Updated Citizen','email':'private@example.org','address':'Secret home address'}).status_code==200
 assert client.post('/api/civilian/profile',json={'name':'Citizen','email':'invalid','address':''}).status_code==422
 r=client.post('/api/civic/reports',data=payload(),files={'images':('camera.jpg',image_bytes(),'image/jpeg')});assert r.status_code==201,r.text
 assert 'civilian_id' not in r.json() and 'email_private' not in r.json()
 assert client.get('/api/civilian/reports').json()[0]['id']==r.json()['id']
 assert repo.get('complaint',r.json()['id'])['civilian_id']==first['id']
 other=TestClient(app);second=sign_in(other,'9000000002')
 assert second['id']!=first['id']
 assert other.get('/api/civilian/saved').json()==[] and other.get('/api/civilian/reports').json()==[]
 assert other.delete('/api/civilian/saved/'+s.json()['id']).status_code==404
 assert other.post('/api/civilian/profile',json={'name':'Thief','email':'','address':'','id':first['id']}).status_code==422
 assert 'Secret home' not in other.get('/api/civic/reports?city_id=delhi').text
 assert client.post('/api/civilian/logout').status_code==200
 assert client.get('/api/civilian/saved').status_code==401
 assert other.get('/api/civilian/session').json()['user']['id']==second['id']

def test_route_checks_accept_only_current_official_notices(client,monkeypatch):
 sign_in(client)
 from backend.api import civilian_travel as t
 common={'id':'official','headline':'Road work','description':'Official road advisory','valid_from':'2026-01-01T00:00:00+00:00','valid_until':'2030-01-01T00:00:00+00:00','source_url':'https://traffic.delhipolice.gov.in/advisory','coordinates':{'latitude':28.601,'longitude':77.25}}
 monkeypatch.setattr(t,'context',lambda city:{'notices':[common,{**common,'id':'fake','source_url':'https://traffic.delhipolice.gov.in.evil.example/notice'},{**common,'id':'unmapped','coordinates':None},{**common,'id':'expired','valid_until':'2020-01-01T00:00:00+00:00'},{**common,'id':'far','coordinates':{'latitude':29.5,'longitude':77.25}}]})
 body={'city_id':'delhi','path':[{'latitude':28.6,'longitude':77.2,'label':'A'},{'latitude':28.6,'longitude':77.3,'label':'B'}]}
 r=client.post('/api/civilian/travel/check',json=body);assert r.status_code==200,r.text
 data=r.json();assert [n['id'] for n in data['route_notices']]==['official']
 assert [n['id'] for n in data['unmapped_city_notices']]==['unmapped']
 assert data['waterlogging_status']=='unknown' and data['model_status']=='not_applicable'
 assert client.post('/api/civilian/travel/check',json={**body,'path':[body['path'][0]]}).status_code==422

def test_civilian_session_never_grants_admin_access(client):
 sign_in(client)
 assert client.get('/api/auth/me').status_code==401
 assert client.get('/api/civic/review?city_id=delhi').status_code==401
 assert client.post('/api/auth/login',json={'username':'admin','password':'110001'}).status_code==200
 # Private civilian storage remains independent of the admin PIN context.
 assert client.get('/api/civilian/session').json()['user']['phone']=='9000000001'
 assert client.get('/api/civilian/saved').status_code==200


def test_stale_cookies_are_cleared_without_granting_access(client):
 client.cookies.set('civicflux_session','expired-or-unknown',domain='testserver.local',path='/')
 r=client.get('/api/cities');assert r.status_code==401
 assert 'civicflux_session=""' in r.headers['set-cookie']
 assert client.get('/api/cities').status_code==200
 client.cookies.set('civicflux_civilian','expired-or-unknown',domain='testserver.local',path='/')
 r=client.get('/api/civilian/session');assert r.json()['user'] is None
 assert 'civicflux_civilian=""' in r.headers['set-cookie']


def test_quick_sms_budget_allows_only_one_attempt(client,monkeypatch):
 monkeypatch.setenv('FAST2SMS_MODE','quick')
 monkeypatch.setenv('FAST2SMS_QUICK_LIMIT','1')
 monkeypatch.setenv('FAST2SMS_QUICK_ACTIVATED_AT','0')
 monkeypatch.delenv('FAST2SMS_OTP_TEMPLATE_ID',raising=False)
 assert client.get('/api/civilian/session').json()['sms_configured']
 id=send(client)
 assert client.post('/api/civilian/otp/send',json={'name':'Other User','phone':'9000000002'}).status_code==429
 assert verify(client,id,SENT['9000000001']).status_code==200

def test_quick_transport_has_one_recipient_and_short_message(monkeypatch):
 import asyncio
 calls=[]
 class Reply:
  status_code=200
  def json(self):return {'return':True,'request_id':'test'}
 class Transport:
  def __init__(self,**kw):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kw):calls.append((url,kw));return Reply()
 monkeypatch.setenv('FAST2SMS_MODE','quick')
 monkeypatch.setattr(c.httpx,'AsyncClient',Transport)
 asyncio.run(real_sms_transport('9000000001','123456'))
 assert len(calls)==1 and calls[0][0]=='https://www.fast2sms.com/dev/bulkV2'
 body=calls[0][1]['json']
 assert body['numbers']=='9000000001' and body['route']=='q'
 assert len(body['message'])<160 and body['message'].isascii() and '123456' in body['message']


def test_quick_provider_activation_error_is_actionable(monkeypatch):
 import asyncio
 class Reply:
  status_code=400
  def json(self):return {'return':False,'status_code':999,'message':'provider text'}
 class Transport:
  def __init__(self,**kw):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,*args,**kw):return Reply()
 monkeypatch.setenv('FAST2SMS_MODE','quick')
 monkeypatch.setattr(c.httpx,'AsyncClient',Transport)
 with pytest.raises(c.HTTPException) as error:asyncio.run(real_sms_transport('9000000001','123456'))
 assert error.value.status_code==503 and 'INR 100' in error.value.detail and 'No OTP was sent' in error.value.detail


@pytest.mark.parametrize('payment_blocked',[True,False])
def test_quick_rejection_budget_and_cooldown(client,monkeypatch,payment_blocked):
 monkeypatch.setenv('FAST2SMS_MODE','quick')
 monkeypatch.setenv('FAST2SMS_QUICK_LIMIT','1')
 monkeypatch.setenv('FAST2SMS_QUICK_ACTIVATED_AT','0')
 async def reject(*args):
  if payment_blocked:raise c.PaymentRequired()
  raise c.HTTPException(503,'Network timeout; delivery unknown')
 monkeypatch.setattr(c,'sms_send',reject)
 body={'name':'Test Citizen','phone':'9000000001'}
 assert client.post('/api/civilian/otp/send',json=body).status_code==503
 assert client.get('/api/civilian/session').json()['user'] is None
 with connection() as db:
  row=db.execute('SELECT id,state FROM civilian_otp').fetchone()
  assert row['state']==('payment_required' if payment_blocked else 'failed')
 assert client.post('/api/civilian/otp/send',json=body).status_code==429
 async def accept(*args):pass
 monkeypatch.setattr(c,'sms_send',accept)
 other=client.post('/api/civilian/otp/send',json={**body,'phone':'9000000002'})
 assert other.status_code==(200 if payment_blocked else 429)
 if payment_blocked:
  assert verify(client,row['id']).status_code==400
  assert client.post('/api/civilian/otp/send',json={**body,'phone':'9000000003'}).status_code==429


def test_quick_budget_retains_older_attempt_history(client,monkeypatch):
 monkeypatch.setenv('FAST2SMS_MODE','quick')
 monkeypatch.setenv('FAST2SMS_QUICK_LIMIT','2')
 monkeypatch.setenv('FAST2SMS_QUICK_ACTIVATED_AT','0')
 first=send(client)
 with connection() as db:db.execute('UPDATE civilian_otp SET created=? WHERE id=?',(time.time()-172800,first))
 send(client,'9000000002')
 with connection() as db:assert db.execute('SELECT count(*) FROM civilian_otp').fetchone()[0]==2
 assert client.post('/api/civilian/otp/send',json={'name':'Other User','phone':'9000000003'}).status_code==429
