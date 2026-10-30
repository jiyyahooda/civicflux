from datetime import date
import pytest
from test_municipal_administration import pool,funding
from test_portal_fixes import login
from backend.db.connection import connection
from backend.api import notifications

def test_area_finance_missing_is_unknown_not_zero(client):
 r=client.get('/api/civic/monetary/delhi?pincode=110001');assert r.status_code==200
 assert r.json()['allocated'] is None and r.json()['spent'] is None
 assert client.get('/api/civic/monetary/delhi?pincode=999999').status_code==422

def test_area_expenditure_is_scoped_and_not_reservation(admin_client):
 c=admin_client;b=funding(c,pool(c));body={'budget_id':b['id'],'amount':1200,'paid_on':date.today().isoformat(),'reference':'Test payment receipt'}
 first=c.post('/api/civic/monetary/expenditures',json=body);assert first.status_code==201
 assert c.post('/api/civic/monetary/expenditures',json=body).json()['id']==first.json()['id']
 c.cookies.clear();a=c.get('/api/civic/monetary/delhi?pincode=110001').json()
 assert a['allocated']==10000 and a['spent']==1200 and a['reserved']==0
 assert c.get('/api/civic/monetary/delhi?pincode=110002').json()['spent'] is None
 assert c.post('/api/civic/monetary/expenditures',json=body).status_code==401
 login(c,'110002');assert c.post('/api/civic/monetary/expenditures',json=body).status_code==403
 login(c,'110001');assert c.post('/api/civic/monetary/expenditures',json={**body,'amount':10000}).status_code==409

@pytest.mark.parametrize('city,pin',[('delhi','110001'),('chennai','600020'),('chandigarh','160017')])
def test_public_network_contains_only_hypothetical_assets(client,city,pin):
 r=client.get('/api/maps/network/'+city+'?pincode='+pin);assert r.status_code==200
 body=r.json();assert body['city_id']==city and body['pincode']==pin and len(body['assets'])==40
 assert all(a['synthetic'] for a in body['assets']) and body['reference']['features']==[]
 assert client.get('/api/maps/geography/'+city).status_code==401

def test_geolocation_never_guesses_outside_supported_area(client):
 body={'latitude':0,'longitude':0,'accuracy':10};assert client.post('/api/civic/location',json=body).json()['status']=='manual_required'
 assert client.post('/api/civic/location',json={**body,'accuracy':2000}).json()['status']=='manual_required'
 with connection() as db:r=db.execute("SELECT latitude,longitude FROM admins WHERE pincode='110001'").fetchone()
 result=client.post('/api/civic/location',json={'latitude':r['latitude'],'longitude':r['longitude'],'accuracy':10}).json()
 assert result['pincode']=='110001' and result['status']=='approximate'

def test_notices_are_exact_pin_only(client,monkeypatch):
 async def absent(*a,**k):return {}
 monkeypatch.setattr(notifications,'weather',absent);monkeypatch.setattr(notifications,'observations',absent)
 notices=[{'id':p,'pincode':p,'headline':'Notice '+p,'description':'Area notice','source_url':'https://example.org/','valid_from':'2026-10-30T00:00:00Z'} for p in ['110001','110002']]
 monkeypatch.setattr(notifications,'context',lambda cid:{'city_id':cid,'notices':notices})
 assert client.get('/api/civic/notifications/delhi').json()['items']==[]
 a=client.get('/api/civic/notifications/delhi?pincode=110001').json()['items']
 assert len(a)==1 and a[0]['pincode']=='110001' and '110002' not in str(a)

def test_receipt_contains_full_description_and_tracking(client,monkeypatch):
 from backend.services import complaint_email
 from test_civic_workflows import report
 sent=[];monkeypatch.setattr(complaint_email,'transport',lambda message:sent.append(message))
 description='Detailed issue observation. '*40
 result=report(client,description=description).json()
 text=sent[0].get_body(preferencelist=('plain',)).get_content()
 assert result['description'] in text and result['id'] in text and 'Blocked drain' in text and '110001' in text
