import asyncio
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import json

import httpx
import pytest
from backend.integrations import imd,air_quality,cpcb,source_http
from backend.services.city_service import city
from backend.services.data_service import normalize
from backend import config
from backend.db.repository import initialize


def weather_feature(station='42182'):
    now=datetime.now(timezone.utc).replace(minute=0,second=0,microsecond=0)
    return {'type':'Feature','geometry':{'type':'Point','coordinates':[77.2,28.58]},
        'properties':{'station_id':int(station),'station':'New Delhi-Safdarjung','dat':now.strftime('%Y-%m-%dZ'),
        'utc':now.hour,'dbtemp':21.0,'rh':78,'24hrlyrain':0,'mslp':1016,'update_time':now.isoformat()}}


def cams_payload():
    now=datetime.now(timezone.utc).replace(minute=0,second=0,microsecond=0)
    return {'latitude':28.7,'longitude':77.2,'current_units':{'time':'unixtime','pm2_5':'μg/m³','pm10':'μg/m³','us_aqi':'USAQI'},
        'current':{'time':int(now.timestamp()),'pm2_5':41.5,'pm10':82,'us_aqi':117},
        'hourly_units':{'time':'unixtime','pm2_5':'μg/m³','pm10':'μg/m³','us_aqi':'USAQI'},
        'hourly':{'time':[int(now.timestamp()),int(now.timestamp())+3600],'pm2_5':[41.5,40.5],'pm10':[82,81],'us_aqi':[117,115]}}


def test_imd_preserves_station_identity_source_time_and_rainfall_period():
    raw=weather_feature();result=normalize(imd.parse_station(raw,city('delhi')),city('delhi'),'IMD')
    assert result['station_id']=='42182' and result['kind']=='observation'
    assert result['readings']['rainfall']['value']==0
    assert '24 hours' in result['readings']['rainfall']['label']
    assert result['age_seconds']<3600 and result['model_input_eligible'] is False
    assert result['coordinates']=={'latitude':28.58,'longitude':77.2}


def test_imd_rejects_unknown_station_and_wrong_coordinates():
    with pytest.raises(ValueError):imd.parse_station(weather_feature('99999'),city('delhi'))
    raw=weather_feature();raw['geometry']['coordinates']=[80.2,13.07]
    with pytest.raises(ValueError):imd.parse_station(raw,city('delhi'))
    raw=weather_feature();raw['properties']['utc']=29
    with pytest.raises(ValueError):imd.parse_station(raw,city('delhi'))


def test_source_freshness_does_not_use_download_time():
    result=imd.parse_station(weather_feature(),city('delhi'))
    result['observed_at']=(datetime.now(timezone.utc)-timedelta(hours=8)).isoformat()
    result['fetched_at']=datetime.now(timezone.utc).isoformat()
    assert normalize(result,city('delhi'),'IMD')['status']=='stale'
    result['observed_at']=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError,match='Future'):normalize(result,city('delhi'),'IMD')


def test_cams_estimate_cannot_be_labeled_station_data_or_indian_aqi():
    result=normalize(air_quality.parse(cams_payload(),city('delhi')),city('delhi'),'CAMS')
    assert result['kind']=='model_estimate' and result['station_id'] is None
    assert result['source']=='CAMS' and result['model_input_eligible'] is False
    assert result['readings']['us_aqi']['unit']=='US AQI' and 'not CPCB' in result['index_standard']
    assert result['series'][1]['is_future'] is True
    broken=cams_payload();broken['current_units']['pm2_5']='index'
    with pytest.raises(ValueError,match='unit'):air_quality.parse(broken,city('delhi'))
    broken=cams_payload();broken['latitude']=13
    with pytest.raises(ValueError,match='grid'):air_quality.parse(broken,city('delhi'))


def test_cpcb_requires_own_key_and_does_not_make_external_calls_without_it(monkeypatch):
    monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','1')
    with pytest.raises(ValueError,match='API key'):asyncio.run(cpcb.fetch(city('delhi')))


def test_cpcb_report_does_not_invent_concentration_units_or_overall_aqi():
    row={'country':'India','state':'Delhi','city':'Delhi','station':'Published station A','latitude':'28.6','longitude':'77.2',
         'last_update':'26-10-2026 18:00:00','pollutant_id':'PM2.5','pollutant_avg':'90'}
    result=cpcb.parse({'records':[row],'total':1},city('delhi'))
    assert result['readings']['reported_PM2.5']['value']==90
    assert result['readings']['reported_PM2.5']['unit']=='publisher value; unit unverified'
    assert 'aqi' not in result['readings'] and 'pm25' not in result['readings']
    wrong={**row,'city':'Chennai'}
    with pytest.raises(ValueError):cpcb.parse({'records':[wrong]},city('delhi'))


def test_partial_source_failure_does_not_remove_weather_or_estimates(client,monkeypatch):
    async def weather(configuration):return imd.parse_station(weather_feature(),configuration)
    async def air(configuration):return air_quality.parse(cams_payload(),configuration)
    monkeypatch.setattr(imd,'fetch',weather);monkeypatch.setattr(air_quality,'fetch',air)
    response=client.get('/api/observations?city_id=delhi')
    assert response.status_code==200
    feeds={f['source']:f for f in response.json()['feeds']}
    assert feeds['IMD']['status']=='fresh' and feeds['CAMS']['kind']=='model_estimate'
    assert feeds['CPCB']['status']=='unavailable' and feeds['CPCB']['requires_configuration'] is True
    assert all(f['model_input_eligible'] is False for f in feeds.values())


def test_cache_serves_stale_evidence_on_network_failure_without_resetting_time(tmp_path,monkeypatch):
    monkeypatch.setattr(config,'DB_PATH',tmp_path/'sources.sqlite3');initialize()
    calls=[]
    class Client:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def get(self,*args,**kwargs):
            calls.append(kwargs)
            if len(calls)>1:raise httpx.ConnectError('network unavailable')
            return httpx.Response(200,json={'temperature':21})
    monkeypatch.setattr(source_http.httpx,'AsyncClient',Client)
    first=asyncio.run(source_http.fetch_json('https://provider.example/data',params={'api-key':'TEST_ONLY_SECRET'},ttl=0))
    second=asyncio.run(source_http.fetch_json('https://provider.example/data',params={'api-key':'TEST_ONLY_SECRET'},ttl=0))
    assert first[0]==second[0] and first[1]==second[1]
    assert second[2] and 'last successful' in second[2]
    assert b'TEST_ONLY_SECRET' not in (tmp_path/'sources.sqlite3').read_bytes()
    result=imd.parse_station(weather_feature(),city('delhi'));result['fetch_warning']=second[2]
    assert normalize(result,city('delhi'),'IMD')['status']=='stale'
