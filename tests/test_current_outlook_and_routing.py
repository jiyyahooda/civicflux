from datetime import date,timedelta
import pytest
from backend.services.outlook_service import parse,FIELDS
from backend.services.city_service import city

def payload():
    dates=[(date(2026,10,27)+timedelta(days=i)).isoformat() for i in range(15)]
    return {'latitude':28.65,'longitude':77.23,'timezone':'Asia/Kolkata','daily_units':FIELDS,
            'daily':{'time':dates,'temperature_2m_max':[30]*15,'temperature_2m_min':[20]*15,
                     'precipitation_sum':[0]*15,'wind_speed_10m_max':[10]*15}}

def test_forecast_dates_are_future_and_not_relabelled():
    rows=parse(payload(),city('delhi'),date(2026,10,27))
    assert len(rows)==14 and rows[0]['date']=='2026-10-28' and rows[-1]['date']=='2026-11-10'
    with pytest.raises(ValueError):parse(payload(),city('delhi'),date(2027,1,1))
    changed=payload();changed['daily_units']={**FIELDS,'precipitation_sum':'inch'}
    with pytest.raises(ValueError):parse(changed,city('delhi'),date(2026,10,27))
    changed=payload();changed['longitude']=0
    with pytest.raises(ValueError):parse(changed,city('delhi'),date(2026,10,27))

def test_forecast_unavailable_has_no_fabricated_rows(client):
    result=client.get('/api/predictions/outlook/delhi').json()
    assert result['status']=='unavailable' and result['rows']==[]
    assert client.get('/api/predictions/outlook/unknown').status_code==404

def test_locality_routing_persistence_and_admin_reassignment(client):
    queues=client.get('/api/authorities?city_id=delhi').json()
    assert len(queues)==9
    body={'city_id':'delhi','locality':'north_west','category':'water','location':'Local test street','description':'A pipe is leaking near the crossing.'}
    from backend import config
    client.post('/api/auth/login',json={'username':config.ADMIN_ID,'password':config.ADMIN_PASSWORD})
    result=client.post('/api/complaints',json=body)
    client.post('/api/auth/logout')
    assert result.status_code==201
    item=result.json();assert item['authority_id']=='delhi:north_west' and item['external_delivery'] is False
    assert client.get('/api/complaints?authority_id=delhi:north_west').json()[0]['id']==item['id']
    route='/api/complaints/'+item['id']+'/route'
    assert client.post(route,json={'locality':'south','note':'Review locality'}).status_code==401
    from backend import config
    assert client.post('/api/auth/login',json={'username':config.ADMIN_ID,'password':config.ADMIN_PASSWORD}).status_code==200
    rerouted=client.post(route,json={'locality':'south','note':'Correct locality after review'})
    assert rerouted.status_code==200 and rerouted.json()['authority_id']=='delhi:south'
    assert any(a['event']=='complaint_routed' for a in client.get('/api/audit').json())
    assert client.post('/api/complaints',json={**body,'locality':'imaginary'}).status_code==422

def test_local_dev_proxy_origin_and_external_origin(client):
    import httpx
    client.base_url=httpx.URL('http://127.0.0.1:8000')
    from backend import config
    client.post('/api/auth/login',json={'username':config.ADMIN_ID,'password':config.ADMIN_PASSWORD})
    assert client.get('/api/auth/me',headers={'host':'127.0.0.1:8000','origin':'http://127.0.0.1:5173'}).status_code==200
    assert client.get('/api/auth/me',headers={'origin':'https://another.example'}).status_code==403
