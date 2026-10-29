"""Read-only snapshot service and bounded, independently cached live indicators."""
import asyncio,gzip,hashlib,json,math,os,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from fastapi import HTTPException
from backend.db.connection import connection
from backend.scope import current
from project_paths import PROJECT_ROOT
from .catalog import SOURCES,ATTR_AIR,ATTR_RIVER
DATA=PROJECT_ROOT/'data';PROCESSED=DATA/'processed'
LAYER_IDS={'che_cma':'datameet/che_cma.geojson','che_wards':'datameet/che_wards.geojson','chd_boundary':'datameet/chd_boundary.geojson','chd_sectors':'datameet/chd_sectors.geojson',**{k:'flood/'+k+'.geojson' for k in ('che_flood_hazard','che_flood_zone_2015','che_flood_points_2015','che_inundation_points')},**{'facilities_'+c:'facilities/facilities_'+c+'.geojson' for c in ('chennai','chandigarh')}}
def manifest():
    path=DATA/'manifest.json'
    if not path.is_file():return {'version':1,'sources':[],'files':{},'live_feeds':[],'evaluated_not_used':[],'status':'NOT FETCHED'}
    value=json.loads(path.read_text())
    # Only catalogue metadata, never local filesystem paths, query payloads or raw API errors.
    fields={'id','title','city','url','resolved_url','pin','resource_id','licence','attribution','mode','status','use','source_last_updated','retrieved_at','records_in','records_out','raw_sha256','byte_size','warning','error','kind_counts','classification_evidence','simplification_degrees','original_gzip_bytes','attribution_url','geometry_repairs','precision_collapses','original_geodesic_area_m2','raw_metadata_sha256','class_area_drift_fraction'}
    value['sources']=[{k:v for k,v in s.items() if k in fields} for s in value['sources']]
    for source in value['sources']:
        if 'error' in source:
            import re
            source['error']=re.sub(r'(?:/Users/|/private/|[A-Za-z]:[\\/])[^\s]+','[local path]',source['error'])
    return value
def pins():
    p=PROCESSED/'derived/pincodes.json'
    return {r['pin']:r for r in json.loads(p.read_text())} if p.exists() else {}
def initialize():
    """Idempotent additive update. Never touch a Delhi row or remove an existing seed."""
    with connection() as db:
        cols={r['name'] for r in db.execute('PRAGMA table_info(admins)')}
        for name,typ in [('coords_quality','TEXT'),('coords_verified','INTEGER')]:
            if name not in cols:db.execute('ALTER TABLE admins ADD COLUMN '+name+' '+typ)
        db.execute('CREATE TABLE IF NOT EXISTS open_data_live_cache(pin TEXT,kind TEXT,body TEXT NOT NULL,fetched REAL NOT NULL,PRIMARY KEY(pin,kind))')
        for p in pins().values():
            if p['city'] not in ('chennai','chandigarh'):continue
            # Only directory-sourced office names may create additional entries; reference coordinates alone cannot invent a locality.
            if p.get('area_name'):
                state='Tamil Nadu' if p['city']=='chennai' else 'Chandigarh'
                db.execute('INSERT OR IGNORE INTO pincodes VALUES (?,?,?,?,?,?,?,?,?,?,?)',(p['pin'],p['city'],p['area_name'],None,state,None,None,next(s['url'] for s in SOURCES if s['id']=='pin_directory'),'2026-10-30',1,'Post-office point; not a PIN boundary.'))
                from uuid import uuid5,NAMESPACE_URL
                db.execute("INSERT OR IGNORE INTO admins(id,pincode,area_name,city_id,is_active,created_at) VALUES (?,?,?,?,1,?)",(str(uuid5(NAMESPACE_URL,'civicflux:postal:'+p['pin'])),p['pin'],p['area_name'],p['city'],datetime.now(timezone.utc).isoformat()))
            db.execute("UPDATE admins SET latitude=?,longitude=?,coordinate_source=?,coords_quality=?,coords_verified=? WHERE pincode=? AND city_id=? AND city_id!='delhi'",(p['lat'],p['lng'],p['source_id'],p['coords_quality'],int(p['coords_verified']),p['pin'],p['city']))
def pin_record(pin,*,ignore_parameter=False):
    scope=current()
    if ignore_parameter:
        if not scope:raise HTTPException(401,'Admin login required')
        pin=scope['pincode']
    elif scope and pin!=scope['pincode']:raise HTTPException(403,'Outside your assigned area')
    if not isinstance(pin,str) or len(pin)!=6 or not pin.isascii() or not pin.isdigit():raise HTTPException(422,'Select a registered six-digit PIN')
    with connection() as db:row=db.execute('SELECT * FROM pincodes WHERE pincode=? AND is_active=1',(pin,)).fetchone()
    if not row:raise HTTPException(404,'PIN is not registered')
    return {**dict(row),**pins().get(pin,{})}
def descriptors(pin):
    p=pin_record(pin);city=p.get('city',p['city_id'])
    if city=='delhi':return {'pin':pin,'city':city,'layers':[],'point':None}
    m=manifest();ss={s['id']:s for s in m['sources']};result=[]
    for id,path in LAYER_IDS.items():
        s=ss.get(id)
        if not s or s['city']!=city or s['status']!='OK' or path not in m['files']:continue
        meta=m['files'][path]
        result.append({'id':id,'title':s['title'],'kind':'facilities' if id.startswith('facilities') else 'flood' if '/flood' in '/'+path else 'boundary','city':city,'source_id':id,'licence':s['licence'],'attribution':s['attribution'],'source_url':s.get('attribution_url') or s.get('resolved_url',s['url']),'feature_count':meta['feature_count'],'default_visible':id in ('che_cma','che_wards','chd_boundary','chd_sectors'),'data_date':s.get('source_last_updated') or s.get('retrieved_at')})
    point=pins().get(pin)
    return {'pin':pin,'city':city,'layers':result,'point':point}
def layer_bytes(id):
    path=LAYER_IDS.get(id);m=manifest()
    if not path or path not in m['files']:raise HTTPException(404,'Layer unavailable')
    s=next((s for s in m['sources'] if s['id']==id and s['status']=='OK'),None)
    if not s:raise HTTPException(404,'Layer unavailable')
    if current() and s['city']!=current()['city_id']:raise HTTPException(404,'Layer unavailable')
    p=PROCESSED/path
    if not p.is_file():raise HTTPException(404,'Layer unavailable')
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=m['files'][path]['sha256']:raise HTTPException(503,'Snapshot integrity check failed')
    return raw,m['files'][path]['sha256']
def exposure(pin):
    p=pin_record(pin)
    if p['city_id']=='delhi':raise HTTPException(404,'Data integration is not enabled for Delhi')
    f=PROCESSED/'derived/pin_exposure.json'
    return json.loads(f.read_text()).get(pin) if f.exists() else None
def reservoirs(pin):
    p=pin_record(pin)
    if p['city_id']!='chennai':raise HTTPException(404,'Reservoir snapshot is for Chennai only')
    f=PROCESSED/'derived/reservoirs.json'
    return json.loads(f.read_text()) if f.exists() else {'status':'unavailable','reservoirs':[],'reason':'All six validated reservoir datasets are not yet available.'}
def category(value):
    if not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:return None
    return next(label for limit,label in [(50,'Good'),(100,'Moderate'),(150,'Unhealthy for Sensitive Groups'),(200,'Unhealthy'),(300,'Very Unhealthy'),(float('inf'),'Hazardous')] if value<=limit)
def number(value):return value if isinstance(value,(int,float)) and math.isfinite(value) and value>=0 else None
def parse_air(raw):
    c=raw['current'];aqi=number(c.get('us_aqi'));pm=number(c.get('pm2_5'));pm10=number(c.get('pm10'))
    if aqi is None and pm is None and pm10 is None:raise ValueError('No air values')
    return {'us_aqi':aqi,'pm2_5':pm,'pm10':pm10,'time':c.get('time'),'category':category(aqi),'model':'CAMS global','resolution_km':45,'attribution':ATTR_AIR}
def parse_river(raw):
    d=raw['daily'];values=d.get('river_discharge',[])[:7];maxima=d.get('river_discharge_max',[])[:7];valid=[number(v) for v in maxima if number(v) is not None]
    if not valid or not values or number(values[0]) is None:raise ValueError('No river values')
    return {'discharge_m3s':number(values[0]),'max_next7_m3s':max(valid),'date':d['time'][0],'note':'Nearest large river in the provider grid; may not be the local river.','attribution':ATTR_RIVER}
async def upstream(kind,p):
    base={'latitude':p['lat'],'longitude':p['lng'],'timezone':'Asia/Kolkata'}
    if kind=='air':url='https://air-quality-api.open-meteo.com/v1/air-quality';params={**base,'current':'us_aqi,pm2_5,pm10','hourly':'us_aqi,pm2_5','forecast_days':2,'domains':'cams_global'}
    else:url='https://flood-api.open-meteo.com/v1/flood';params={**base,'daily':'river_discharge,river_discharge_max','forecast_days':7}
    async with httpx.AsyncClient(timeout=2.8,follow_redirects=False) as client:
        for attempt in range(3):
            try:
                r=await client.get(url,params=params);r.raise_for_status();return (parse_air if kind=='air' else parse_river)(r.json())
            except Exception:
                if attempt==2:raise
                await asyncio.sleep(.05*2**attempt)
async def conditions(pin):
    p=pin_record(pin)
    if p['city_id']=='delhi':raise HTTPException(404,'Existing Delhi conditions remain unchanged')
    async def part(kind):
        with connection() as db:cached=db.execute('SELECT body,fetched FROM open_data_live_cache WHERE pin=? AND kind=?',(pin,kind)).fetchone()
        if cached and time.time()-cached['fetched']<1800:return {**json.loads(cached['body']),'retrieved_at':datetime.fromtimestamp(cached['fetched'],timezone.utc).isoformat(),'stale':False}
        try:
            if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1' or 'lat' not in p:raise ValueError('Feed disabled or no validated postal reference')
            async with asyncio.timeout(3):value=await upstream(kind,p)
            stamp=time.time()
            with connection() as db:db.execute('INSERT INTO open_data_live_cache VALUES (?,?,?,?) ON CONFLICT(pin,kind) DO UPDATE SET body=excluded.body,fetched=excluded.fetched',(pin,kind,json.dumps(value,allow_nan=False),stamp))
            return {**value,'retrieved_at':datetime.fromtimestamp(stamp,timezone.utc).isoformat(),'stale':False}
        except Exception:
            if cached:return {**json.loads(cached['body']),'retrieved_at':datetime.fromtimestamp(cached['fetched'],timezone.utc).isoformat(),'stale':True}
            return None
    air,river=await asyncio.gather(part('air'),part('river'))
    stamps=[v['retrieved_at'] for v in (air,river) if v]
    return {'pin':pin,'air':air,'river':river,'updated_at':min(stamps) if stamps else None,'stale':any(v is None or v['stale'] for v in (air,river))}
