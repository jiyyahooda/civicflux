import json
from backend.integrations.waqi import normalize_stations
from backend.graph import dependencies
from backend.db.connection import connection

def test_demo_geography_retains_real_reference_and_synthetic_asset_scope(client):
 body=client.get('/api/maps/geography/delhi').json()
 assert body['status']=='available' and body['synthetic'] and body['real_incidents'] is False
 assert len(body['sources'])==8 and len(body['assets'])==40
 graph=dependencies()
 assert body['graph_fingerprint']==graph['fingerprint']
 assert {a['id'] for a in body['assets']}=={n['id'] for n in graph['nodes']}
 assert all(a['synthetic'] and 'not a surveyed' in a['location_status'] for a in body['assets'])
 assert all(f['properties']['condition']=='unknown' and f['properties']['source_url'].startswith('https://www.openstreetmap.org/') for f in body['reference']['features'])
 assert client.get('/api/maps/geography/chennai').json()['status']=='unavailable'
 assert client.get('/api/maps/geography/unknown').status_code==404

def test_station_parser_rejects_missing_values_invalid_positions_and_duplicates():
 row={'uid':1,'lat':28.6,'lon':77.2,'aqi':'147','station':{'name':'Test station','time':'2026-10-28 00:00:00'}}
 rows=normalize_stations([row,row,{**row,'uid':2,'aqi':'-'},{**row,'uid':3,'lat':900},{**row,'uid':4,'aqi':'NaN'}])
 assert len(rows)==1 and rows[0]['aqi']==147
 assert 'pm25' not in rows[0]

def test_waqi_live_response_excludes_credentials_and_is_not_archived(client,monkeypatch):
 import backend.integrations.waqi as module
 monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','1');monkeypatch.setenv('WAQI_API_TOKEN','private-test-token')
 class Result:
  status_code=200
  def __init__(self,payload):self.payload=payload
  def json(self):return self.payload
 class HTTP:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def get(self,url,params):
   assert url.startswith('https://api.waqi.info/') and params['token']=='private-test-token'
   if '/feed/' in url:return Result({'status':'ok','data':{'aqi':147,'city':{'name':'Delhi reference'},'time':{'iso':'2026-10-28T00:00:00+05:30'},'attributions':[{'name':'Test EPA','url':'https://example.org/epa'}],'iaqi':{'pm25':{'v':147}}}})
   return Result({'status':'ok','data':[{'uid':1,'lat':28.6,'lon':77.2,'aqi':'147','station':{'name':'Test station','time':'2026-10-28 00:00:00'}}]})
 monkeypatch.setattr(module.httpx,'AsyncClient',HTTP)
 response=client.get('/api/maps/air/delhi');body=response.json()
 assert body['status']=='available' and len(body['stations'])==1
 assert response.headers['cache-control']=='no-store'
 assert 'private-test-token' not in response.text and 'iaqi' not in body
 assert body['attributions'][0]['name']=='Test EPA'
 with connection() as db:
  table=db.execute("SELECT name FROM sqlite_master WHERE name='source_cache'").fetchone()
  if table:assert db.execute('SELECT count(*) FROM source_cache').fetchone()[0]==0

def test_waqi_disabled_or_missing_key_fails_closed(client,monkeypatch):
 monkeypatch.delenv('WAQI_API_TOKEN',raising=False)
 body=client.get('/api/maps/air/delhi').json()
 assert body['status']=='unavailable' and body['stations']==[]
 assert client.get('/api/maps/air/unknown').status_code==404

def test_volume_interpretation_is_explicit_rule_with_validated_capacity(client):
 for volume,label in [(300,'Low'),(600,'Moderate'),(960,'High'),(1300,'Over assumed capacity')]:
  response=client.post('/api/maps/traffic-interpretation',json={'vehicles_per_hour':volume,'assumed_capacity':1200})
  assert response.status_code==200 and response.json()['category']==label
  assert 'not an ML' in response.json()['basis']
 assert client.post('/api/maps/traffic-interpretation',json={'vehicles_per_hour':10,'assumed_capacity':0}).status_code==422
 assert client.post('/api/maps/traffic-interpretation',json={'vehicles_per_hour':-1,'assumed_capacity':100}).status_code==422

def test_precipitation_configuration_and_bounded_tiles_do_not_expose_key(client,monkeypatch):
 monkeypatch.delenv('OPENWEATHERMAP_API_KEY',raising=False)
 assert client.get('/api/maps/weather-configuration').json()=={'precipitation_tiles_configured':False}
 assert client.get('/api/maps/rain-tiles/10/100/100.png').status_code==503
 assert client.get('/api/maps/rain-tiles/30/1/1.png').status_code==422


def test_scenario_download_carries_only_declared_simulation_inputs(client):
 response=client.get('/api/maps/geography/delhi/download?rain_mm=120&blockage=0.7&volume=1500&capacity=1200&outages=pump_0,drainage_1')
 assert response.status_code==200 and 'attachment' in response.headers['content-disposition']
 body=response.json();assert body['synthetic'] and body['real_incidents'] is False
 assert body['assumptions']['rain_mm']==120 and body['declared_outages']==['pump_0','drainage_1']
 assert client.get('/api/maps/geography/delhi/download?capacity=0').status_code==422
 assert client.get('/api/maps/geography/delhi/download?outages=unknown').status_code==422
