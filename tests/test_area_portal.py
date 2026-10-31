import pytest
pytestmark=pytest.mark.usefixtures("civilian_account")
"""Postal-login, isolation, SMTP and forecast regressions using disposable state."""
import hashlib,json,time
from datetime import datetime,timedelta,timezone
import pytest
from backend.db.connection import connection
from backend.db import repository as repo
from backend.services import complaint_email as mail
from test_civic_workflows import report

def login(c,pin='110001',name='admin'):
 return c.post('/api/auth/login',json={'username':name,'password':pin})

def test_area_seed_unique_public_pin_identities(client):
 with connection() as db:
  rows=db.execute('SELECT * FROM admins').fetchall()
  assert len(rows)==111 and len({r['pincode'] for r in rows})==111
  assert all(r['username']=='admin' and len(r['pincode'])==6 for r in rows)
 assert login(client,'110001').status_code==200
 profile=client.get('/api/auth/me').json()['profile']
 assert profile['pincode']=='110001' and profile['role']=='area_admin'
 assert len(profile['assignments'])==1
 assert login(client,'110001','other').status_code==401
 assert login(client,'999999').status_code==401
 assert login(client,'001').status_code==401

def test_area_lockout_ip_cannot_bypass_by_changing_username(client):
 for i in range(5):assert login(client,'999999',str(i)).status_code==401
 assert login(client).status_code==429
 with connection() as db:
  assert db.execute('SELECT count(*) FROM area_login_audit WHERE success=0').fetchone()[0]==5
  db.execute('UPDATE auth_attempts SET last_attempt=?',(time.time()-901,))
 assert login(client).status_code==200

def test_session_cookie_logout_idle_and_deactivation(client):
 res=login(client);cookie=res.headers['set-cookie'].lower()
 assert 'httponly' in cookie and 'samesite=strict' in cookie
 with connection() as db:db.execute('UPDATE sessions SET last_seen=?',(time.time()-1801,))
 assert client.get('/api/auth/me').status_code==401
 assert client.get('/api/civic/context/delhi').status_code==401
 client.cookies.clear();assert login(client).status_code==200
 assert client.post('/api/auth/logout').status_code==200
 assert client.get('/api/auth/me').status_code==401
 assert login(client).status_code==200
 assert client.post('/api/municipal/administrators',json={'pincode':'110002','is_active':False}).status_code==403
 assert client.post('/api/municipal/administrators',json={'pincode':'110001','is_active':False}).status_code==200
 client.cookies.clear();assert login(client).status_code==401

def test_admin_reads_only_own_even_on_public_routes_and_images(client):
 x=report(client,postal_code='110001',title='Own area drain').json()
 y=report(client,postal_code='110002',title='Other area drain').json()
 z=repo.append('complaint',{'city_id':'delhi','title':'Unassigned','status':'submitted'})
 assert login(client).status_code==200
 for path in ['/api/civic/reports?city_id=delhi','/api/civic/review?city_id=delhi','/api/complaints']:
  response=client.get(path);assert response.status_code==200,response.text
  assert {r['id'] for r in response.json()}=={x['id']}
 assert client.get('/api/civic/reports/'+y['id']).status_code==404
 assert client.get(y['images'][0]['url']).status_code==404
 assert client.get('/api/civic/reports/'+z['id']).status_code==404
 assert client.get('/api/civic/reports/'+x['id']).status_code==200
 assert client.post('/api/complaints/'+y['id'],json={'status':'under_review','note':'Cross area attempt'}).status_code==404
 for path in ['/api/civic/reports?city_id=chennai','/api/municipal/local/delhi?pincode=110002','/api/predictions/outlook/chennai','/api/maps/air/chennai']:
  assert client.get(path).status_code==403,path
 assert len(client.get('/api/cities').json())==1
 assert client.get('/api/cities/delhi').json()['pincode']=='110001'

def test_non_admin_cannot_use_simulation_or_review(client):
 for path in ['/api/maps/geography/delhi','/api/maps/geography/delhi/download','/api/scenarios','/api/municipal/administrators','/api/civic/review?city_id=delhi']:
  assert client.get(path).status_code==401,path
 assert client.post('/api/assessments/flood',json={'city_id':'delhi'}).status_code==401
 assert login(client).status_code==200
 body=client.get('/api/maps/geography/delhi').json()
 assert {a['pincode'] for a in body['assets']}=={'110001'}
 assert body['reference']['features']==[]
 assert max(abs(a['latitude']-client.get('/api/auth/me').json()['profile']['latitude']) for a in body['assets'])<.004

def test_postal_weather_provider_uses_session_reference(client,monkeypatch):
 assert login(client).status_code==200
 from backend.services import outlook_service as out
 calls=[]
 async def fetch(url,params,ttl):
  calls.append(params)
  raise ValueError('Mock provider unavailable')
 monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','1');monkeypatch.setattr(out,'fetch_json',fetch)
 result=client.get('/api/predictions/outlook/delhi').json()
 with connection() as db:p=db.execute("SELECT * FROM admins WHERE pincode='110001'").fetchone()
 assert result['pincode']=='110001' and result['status']=='unavailable'
 assert calls[0]['latitude']==p['latitude'] and calls[0]['longitude']==p['longitude']
 assert client.get('/api/predictions/outlook/chennai').status_code==403

def test_unknown_postal_coordinates_never_use_city_centre(client):
 assert login(client,'160021').status_code==200
 response=client.get('/api/civic/weather/chandigarh').json()
 assert response['current'] is None and response['status']=='unavailable'
 assert client.get('/api/cities').json()[0]['map_reference'] is None
 assert client.get('/api/maps/geography/chandigarh').json()['status']=='unavailable'

def test_confirmation_email_multipart_escaped_deduplicated(client,monkeypatch):
 sent=[];monkeypatch.setattr(mail,'transport',sent.append)
 result=report(client,description='<script>example</script> blocked drain.').json()
 assert result['confirmation_email']=='sent' and len(sent)==1
 msg=sent[0]
 assert result['id'] in msg['Subject'] and 'Tracking ID' in msg.get_body(preferencelist=('plain',)).get_content()
 html=msg.get_body(preferencelist=('html',)).get_content()
 assert '&lt;script&gt;' in html and '<script>' not in html
 assert msg['From']=='test@example.org'
 assert report(client,description='<script>example</script> blocked drain.').json()['id']==result['id']
 assert len(sent)==1

def test_email_failure_preserves_registration_and_hides_credentials(client,monkeypatch,caplog):
 def fail(message):raise RuntimeError('secret-password-must-not-appear')
 monkeypatch.setattr(mail,'transport',fail)
 response=report(client);assert response.status_code==201
 body=response.json();assert body['confirmation_email']=='failed'
 assert client.get('/api/civic/reports/'+body['id']).status_code==200
 assert 'secret-password' not in caplog.text
 assert client.post('/api/civic/reports',data={'email':'bad'}).status_code==422
 assert client.post('/api/send-email',json={'to':'anything@example.org'}).status_code==404

def test_email_abuse_limits_recipient_and_ip(client,monkeypatch):
 sent=[];monkeypatch.setattr(mail,'transport',sent.append)
 for i in range(4):
  response=report(client,title='Report number '+str(i))
  assert response.status_code==201
  assert response.json()['confirmation_email']==('sent' if i<3 else 'rate_limited')
 assert len(sent)==3
 for i in range(8):report(client,title='Different recipient '+str(i),email=f'other{i}@example.org')
 assert len(sent)==10

def test_database_migration_hides_unassigned_and_has_no_random_password(client):
 # Re-run the migration on representative old records in an isolated DB.
 a=repo.append('civic_notice',{'city_id':'delhi','area':'Connaught Place','headline':'Legacy locality record'})
 b=repo.append('civic_notice',{'city_id':'delhi','area':'Unknown historic area','headline':'Unassigned record'})
 with connection() as db:db.execute('DELETE FROM schema_migrations WHERE version=2')
 from backend.db.areas import migrate
 migrate();assert repo.get('civic_notice',a['id'])['pincode']=='110001'
 assert repo.get('civic_notice',b['id'])['pincode'] is None
 assert login(client).status_code==200
 assert client.get('/api/municipal/local/delhi').status_code==200
 with connection() as db:assert db.execute('SELECT count(*) FROM admins').fetchone()[0]==111
