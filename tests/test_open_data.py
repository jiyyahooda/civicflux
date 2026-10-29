"""Scientific fixtures, real snapshot integrity, scope and upstream failure isolation."""
import asyncio,copy,hashlib,json,time
from pathlib import Path
import pytest
from shapely.geometry import Point,box,mapping,shape
from backend.db.connection import connection
from backend.data_integration import service
from backend.data_integration.catalog import REFERENCE,CAPACITIES
from scripts import data_pipeline as pipeline

@pytest.mark.parametrize('value,expected',[(0,'Good'),(50,'Good'),(51,'Moderate'),(100,'Moderate'),(101,'Unhealthy for Sensitive Groups'),(150,'Unhealthy for Sensitive Groups'),(151,'Unhealthy'),(200,'Unhealthy'),(201,'Very Unhealthy'),(300,'Very Unhealthy'),(301,'Hazardous'),(-1,None),(float('nan'),None),(None,None)])
def test_aqi_boundaries(value,expected):assert service.category(value)==expected

def test_distance_units_and_axis_order():
    assert pipeline.haversine((0,0),(0,1))==pytest.approx(111.195,abs=.01)
    for id,point,wrong in [('che_cma',(80.2707,13.0827),(13.0827,80.2707)),('chd_boundary',(76.7794,30.7333),(30.7333,76.7794))]:
        raw,_=service.layer_bytes(id);features=json.loads(raw)['features']
        assert any(shape(f['geometry']).covers(Point(*point)) for f in features)
        assert not any(shape(f['geometry']).covers(Point(*wrong)) for f in features)

def test_coordinate_resolution_rejects_cross_zone_placeholder_and_typos():
    layers={id:json.loads(service.layer_bytes(id)[0]) for id in ('che_wards','chd_sectors','chd_boundary')}
    def row(lat,lon,pin='600020'):return {'Pincode':pin,'Latitude':str(lat),'Longitude':str(lon)}
    # Adyar placeholder in T Nagar, and severe latitude typo, cannot influence a valid Adyar point.
    value=pipeline.resolve_pin('600020',[row(13.0453611,80.2376111),row(12.1640833,80.25),row(13.00103,80.25731)],layers)
    assert (value['lat'],value['lng'])==(13.00103,80.25731)
    expected=next(f for f in layers['che_wards']['features'] if f['properties']['ward_no']==176)
    assert shape(expected['geometry']).contains(Point(value['lng'],value['lat']))
    anna=pipeline.resolve_pin('600040',[row(13.0453611,80.2376111,'600040')],layers)
    assert anna['coords_quality']=='polygon-centroid' and not anna['coords_verified']
    assert any(f['properties']['zone_name']=='ANNANAGAR' and shape(f['geometry']).covers(Point(anna['lng'],anna['lat'])) for f in layers['che_wards']['features'])
    chd=pipeline.resolve_pin('160002',[row(30.692051,76.69841,'160002'),row(30.69,75.9453611,'160002'),row(30.69136,76.79257,'160002')],layers)
    assert (chd['lat'],chd['lng'])==(30.69136,76.79257)

def test_kml_schema_data_survives_duplicate_fid_and_missing_remark(tmp_path):
    path=tmp_path/'fixture.kml';path.write_text('<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'+''.join('<Placemark><ExtendedData><SchemaData>'+''.join('<SimpleData name="'+k+'">'+v+'</SimpleData>' for k,v in {'OBJECTID_1':str(i),'F_ID':'1','DEPTH':str(5+i),'F_REMARKS':'  road water  ' if i else ''}.items())+'</SchemaData></ExtendedData><Point><coordinates>80.27,13.08,0</coordinates></Point></Placemark>' for i in range(3))+'</Document></kml>')
    rows=list(pipeline.parse_kml(path));assert len(rows)==3
    assert rows[0][0]['coordinates']==[80.27,13.08]
    assert rows[1][1]['DEPTH']=='6' and rows[1][1]['F_REMARKS'].strip()=='road water'
    assert len({p['OBJECTID_1'] for _,p in rows})==3
    assert len({p['F_ID'] for _,p in rows})==1
    assert pipeline.inundation_properties(rows[0][1])=={'id':'0','depth_in':5.0,'remark':None}
    assert pipeline.inundation_properties(rows[1][1])['remark']=='road water'

def test_lake_csv_structures_and_nulls():
    assert pipeline.lake_csv('Date,Storage mcft\n01/01/2003,100\n01/02/2003,\n')==[{'month':'2003-01','mcft':100.0},{'month':'2003-02','mcft':None}]
    wide='Year,Jan (mcft),Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec\n2020,,,,,,,,,,,,257\n'
    out=pipeline.lake_csv(wide);assert len(out)==12 and out[-1]=={'month':'2020-12','mcft':257.0} and out[0]['mcft'] is None
    with pytest.raises(ValueError,match='Duplicate'):pipeline.lake_csv('Date,Storage\n01/01/2003,1\n02/01/2003,2\n')
    with pytest.raises(ValueError):pipeline.lake_csv('Date,Storage,Level\n01/01/2003,1,2\n')
    with pytest.raises(ValueError):pipeline.lake_csv('Date,Storage\n01/01/2003,-1\n')
    assert sum(CAPACITIES.values())==13222

def test_exposure_missing_data_is_not_zero_or_safe():
    p={'pin':'600020','city':'chennai','lat':13.0,'lng':80.25}
    empty=pipeline.exposure(p,{})
    assert empty['hazard_class_at_point'] is None and empty['flood_points_2015_within_r'] is None
    assert empty['facilities_within_r'] is None and empty['in_2015_inundation_zone'] is None
    poly=pipeline.feature('f',mapping(box(80.24,12.99,80.26,13.01)),{'class':'Very High'})
    point=pipeline.feature('a',{'type':'Point','coordinates':[80.25,13]},{'depth_in':12})
    result=pipeline.exposure(p,{'che_flood_hazard':pipeline.collection([poly]),'che_inundation_points':pipeline.collection([point])})
    assert result['hazard_class_at_point']=='Very High' and result['max_depth_in_within_r']==12

def test_facility_named_dedup_and_required_kinds():
    def element(id,kind,lat,lon,name=None):return {'id':id,'type':'node','lat':lat,'lon':lon,'tags':{'amenity':kind,**({'name':name} if name else {})}}
    raw={'elements':[element(1,'hospital',13,80.25),element(2,'hospital',13.00001,80.25001,'Verified hospital'),element(3,'fire_station',13.01,80.25,'Fire station'),element(4,'police',13,80.26,'Police station')]}
    boundary=pipeline.collection([pipeline.feature('b',mapping(box(80.2,12.9,80.3,13.1)),{})])
    out,counts=pipeline.facilities('chennai',raw,boundary)
    assert counts=={'hospital':1,'fire_station':1,'police':1}
    assert any(f['properties']['name']=='Verified hospital' for f in out['features'])

def test_small_offline_build_is_byte_deterministic(tmp_path,monkeypatch):
    for key,value in [('ROOT',tmp_path),('DATA',tmp_path/'data'),('RAW',tmp_path/'data/raw'),('OUT',tmp_path/'data/processed'),('MANIFEST',tmp_path/'data/manifest.json')]:monkeypatch.setattr(pipeline,key,value)
    pipeline.build();first={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    pipeline.build();second={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert first==second and pipeline.verify()

def login(client,pin):assert client.post('/api/auth/login',json={'username':'admin','password':pin}).status_code==200

def test_public_allowlists_gzip_etag_and_manifest(client):
    assert client.get('/api/data/layers?pin=999999').status_code==404
    assert client.get('/api/data/layers?pin=bad').status_code==422
    layers=client.get('/api/data/layers?pin=600001').json();assert {x['id'] for x in layers['layers']} >= {'che_wards','che_cma'}
    result=client.get('/api/data/layer/che_wards',headers={'Accept-Encoding':'gzip'})
    assert result.status_code==200 and result.headers['content-encoding']=='gzip'
    assert result.headers['cache-control']=='public, max-age=3600' and len(result.json()['features'])==200
    assert client.get('/api/data/layer/che_wards',headers={'If-None-Match':result.headers['etag']}).status_code==304
    assert client.get('/api/data/layer/unknown').status_code==404
    m=client.get('/api/data/manifest').text;assert '/Users/' not in m and 'SMTP_PASS' not in m and 'local_path' not in m

def test_admin_pin_parameter_is_ignored_but_other_scope_is_denied(client):
    login(client,'600001')
    assert client.get('/api/admin/data/layers?pin=160017').json()['pin']=='600001'
    assert client.get('/api/admin/live/conditions?pin=160017').json()['pin']=='600001'
    assert client.get('/api/data/layers?pin=160017').status_code==403
    assert client.get('/api/data/layer/chd_boundary').status_code==404
    client.cookies.clear();assert client.get('/api/admin/data/layers').status_code==401

def test_live_independent_cache_and_stale_fallback(client,monkeypatch):
    monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','1')
    async def good(kind,p):return {'us_aqi':50,'pm2_5':10,'pm10':15,'time':'2026-10-30','category':'Good'} if kind=='air' else {'discharge_m3s':2,'max_next7_m3s':3,'date':'2026-10-30'}
    monkeypatch.setattr(service,'upstream',good)
    result=client.get('/api/live/conditions?pin=600001').json();assert result['air']['us_aqi']==50 and not result['stale']
    with connection() as db:db.execute('UPDATE open_data_live_cache SET fetched=?',(time.time()-1900,))
    async def partial(kind,p):
        if kind=='air':raise RuntimeError('secret-token-must-not-leak')
        return await good(kind,p)
    monkeypatch.setattr(service,'upstream',partial)
    result=client.get('/api/live/conditions?pin=600001');body=result.json()
    assert body['air']['stale'] and not body['river']['stale'] and body['stale']
    assert 'secret-token' not in result.text

def test_live_upstream_deadline_no_data_and_delhi_unchanged(client,monkeypatch):
    monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','1')
    async def blocked(*args):await asyncio.sleep(20)
    monkeypatch.setattr(service,'upstream',blocked)
    before=time.monotonic();result=client.get('/api/live/conditions?pin=600001')
    assert time.monotonic()-before<3.5
    assert result.json()['air'] is None and result.json()['river'] is None
    assert client.get('/api/data/layers?pin=110001').json()['layers']==[]
    assert client.get('/api/live/conditions?pin=110001').status_code==404

def test_seed_preservation_and_idempotence(client):
    with connection() as db:
        before=[dict(r) for r in db.execute("SELECT * FROM admins WHERE city_id='delhi' ORDER BY pincode")]
        total=db.execute('SELECT count(*) FROM admins').fetchone()[0]
    service.initialize();service.initialize()
    with connection() as db:
        assert [dict(r) for r in db.execute("SELECT * FROM admins WHERE city_id='delhi' ORDER BY pincode")]==before
        assert db.execute('SELECT count(*) FROM admins').fetchone()[0]==total
        assert len(before)==77
    for pin in REFERENCE:
        point=service.pins()[pin];lat,lon=REFERENCE[pin]
        assert abs(point['lat']-lat)<=.002 and abs(point['lng']-lon)<=.002
