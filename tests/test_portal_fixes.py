"""Role, city-wide-reference, notification identity, city mapping and mail acceptance checks."""
import json,smtplib
from datetime import datetime,timezone
from email.message import EmailMessage
import pytest
from backend.api import notifications
from backend.db.connection import connection
from backend.services import complaint_email as mail
from backend.services.complaint_email import transport as gmail_transport
from test_civic_workflows import report
def login(c,pin):
    c.cookies.clear();assert c.post('/api/auth/login',json={'username':'admin','password':pin}).status_code==200

def test_city_infra_requires_login_and_does_not_leak_through_public_context(client):
    for path in ['/api/admin/city-infra','/api/reference/delhi','/api/reference/delhi/source']:assert client.get(path).status_code==401
    assert client.get('/api/civic/context/delhi').json()['reference'] is None

@pytest.mark.parametrize('city,a,b',[('delhi','110001','110002'),('chandigarh','160017','160021'),('chennai','600001','600020')])
def test_city_reference_is_identical_across_postal_areas(client,city,a,b):
    login(client,a);first=client.get('/api/admin/city-infra').json()
    login(client,b);second=client.get('/api/admin/city-infra?pin=999999').json()
    assert first==second and first['city_id']==city and 'pincode' not in first
    if city=='delhi':assert len(first['reference']['budget'])==16
    else:assert first['reference'] is None and first['layers']
    assert client.get('/api/reference/'+('delhi' if city!='delhi' else 'chennai')).status_code==404

@pytest.mark.parametrize('pin,city',[('600020','chennai'),('160017','chandigarh')])
def test_synthetic_maps_keep_correct_city_not_delhi(client,pin,city):
    login(client,pin);body=client.get('/api/maps/geography/'+city).json()
    assert body['city_id']==city and body['synthetic'] and not body['real_incidents']
    assert body['sources']==[] and body['reference']['features']==[]
    assert all(a['pincode']==pin and a['synthetic'] for a in body['assets'])
    response=client.get('/api/maps/geography/'+city+'/download')
    assert city in response.headers['content-disposition']

@pytest.mark.parametrize('city,pin,lat,lon',[('chennai','600020','13.00103','80.25731'),('chandigarh','160017','30.74208','76.78336'),('delhi','110001','28.62190','77.21282')])
def test_registered_pins_are_supported_for_actual_report_submission(client,city,pin,lat,lon):
    pins=client.get('/api/civic/postal/'+city).json()['records']
    assert pin in {p['pin'] for p in pins}
    result=report(client,city_id=city,postal_code=pin,latitude=lat,longitude=lon).json()
    assert result['city_id']==city and result['postal_code']==pin and result['id']

def test_notification_ids_use_event_times_not_polling_times_and_ignore_other_cities():
    stamp='2026-10-30T00:00:00+05:30'
    w={'city_id':'chennai','status':'available','observed_at':stamp,'source_url':'https://open-meteo.com/','current':{'temperature_2m':41,'precipitation':12}}
    o={'city_id':'chennai','feeds':[{'source':'CAMS','status':'fresh','observed_at':stamp,'provider_url':'https://open-meteo.com/','readings':{'us_aqi':{'value':151}}}]}
    civic={'city_id':'chennai','notices':[{'id':'notice-a','headline':'Published notice','description':'Actual imported notice','source_url':'https://chennaicorporation.gov.in/','valid_from':stamp}]}
    first=notifications.build_notifications('chennai',w,o,civic,[])
    assert len(first)==4 and len({n['id'] for n in first})==4
    assert first==notifications.build_notifications('chennai',{**w,'checked_at':'different'},o,civic,[])
    assert notifications.build_notifications('chandigarh',w,o,civic,[])==[]
    assert notifications.build_notifications('chennai',{**w,'status':'stale'},o,{'city_id':'chennai','notices':[]},[])==[n for n in first if n['title'].startswith('Modelled')]

def test_notification_endpoint_tracks_only_requested_report_updates_and_never_email(client,monkeypatch):
    result=report(client).json()
    async def absent(cid):return {'city_id':cid}
    monkeypatch.setattr(notifications,'weather',absent);monkeypatch.setattr(notifications,'observations',absent)
    monkeypatch.setattr(notifications,'context',lambda cid:{'city_id':cid,'notices':[]})
    assert client.get('/api/civic/notifications/delhi').json()['items']==[]
    response=client.get('/api/civic/notifications/delhi?tracking_ids='+result['id']);body=response.json()
    assert len(body['items'])==1 and body['poll_seconds']==60
    assert 'email_private' not in response.text and 'example.org' not in response.text
    assert client.get('/api/civic/notifications/chennai?tracking_ids='+result['id']).json()['items']==[]
    assert client.get('/api/civic/notifications/unknown').status_code==404

def test_email_provider_acceptance_and_attempt_status_are_explicit(client,monkeypatch):
    observed=[]
    def accepted(message):
        with connection() as db:observed.append(dict(db.execute('SELECT * FROM complaint_mail').fetchone()))
        assert 'not been submitted to a government complaint system' in message.get_body(preferencelist=('plain',)).get_content()
    monkeypatch.setattr(mail,'transport',accepted)
    result=report(client).json();assert result['confirmation_email']=='sent'
    assert observed[0]['status']=='sending' and observed[0]['attempt_count']==1
    with connection() as db:row=dict(db.execute('SELECT * FROM complaint_mail WHERE report_id=?',(result['id'],)).fetchone())
    assert row['provider_accepted']==1 and row['attempt_count']==1 and row['failure_code'] is None
    assert report(client).json()['id']==result['id']
    with connection() as db:assert db.execute('SELECT attempt_count FROM complaint_mail WHERE report_id=?',(result['id'],)).fetchone()[0]==1

def test_invalid_sender_header_cannot_turn_saved_report_into_server_error(client,monkeypatch):
    monkeypatch.setenv('SMTP_USER','invalid\nsender')
    response=report(client);assert response.status_code==201 and response.json()['confirmation_email']=='failed'
    with connection() as db:row=dict(db.execute('SELECT * FROM complaint_mail').fetchone())
    assert row['provider_accepted']==0 and row['failure_code']=='ValueError'

def test_smtp_refusal_is_not_reported_as_accepted(monkeypatch):
    class SMTP:
        def __init__(self,*a,**k):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def login(self,*a):pass
        def send_message(self,*a):return {'rejected@example.org':(550,b'rejected')}
    monkeypatch.setattr(mail.smtplib,'SMTP_SSL',SMTP);monkeypatch.setenv('SMTP_PASS','test-only-not-a-real-password')
    msg=EmailMessage();msg['To']='rejected@example.org';msg.set_content('Test')
    with pytest.raises(smtplib.SMTPRecipientsRefused):gmail_transport(msg)

@pytest.mark.parametrize('cid',['delhi','chennai','chandigarh'])
def test_weather_uses_correct_city_reference_and_accepts_india_timezone_alias(client,monkeypatch,cid):
    from backend.integrations import weather
    from backend.services.city_service import city
    calls=[];today=datetime.now(__import__('zoneinfo').ZoneInfo('Asia/Kolkata')).date().isoformat()
    async def fetch(url,params,**kwargs):
        calls.append(params)
        return {'timezone':'Asia/Calcutta','latitude':params['latitude'],'longitude':params['longitude'],'current_units':weather.CURRENT,'current':dict(temperature_2m=30,apparent_temperature=32,relative_humidity_2m=75,precipitation=0,wind_speed_10m=10,weather_code=2,time=today+'T12:00'), 'daily_units':dict(temperature_2m_max='°C',temperature_2m_min='°C',precipitation_sum='mm',precipitation_probability_max='%',weather_code='wmo code'),'daily':dict(time=[today],temperature_2m_max=[32],temperature_2m_min=[26],precipitation_sum=[0],precipitation_probability_max=[0],weather_code=[2])},today,None
    monkeypatch.setattr(weather,'fetch_json',fetch);monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','1')
    body=client.get('/api/civic/weather/'+cid).json();assert body['city_id']==cid and body['current']['temperature_2m']==30
    expected=city(cid)['map_reference'];assert calls[0]['latitude']==expected['latitude'] and calls[0]['longitude']==expected['longitude']
