"""Official public SYNOP layer referenced by IMD's public homepage."""
import os
import math
from datetime import datetime, timezone
from .source_http import fetch_json

WFS_URL='https://reactjs.imd.gov.in/geoserver/imd/ows'
REFERENCE='https://mausam.imd.gov.in/index_en.php?lang=en'


def parse_station(feature, configuration):
    p=feature['properties'];station_id=str(p['station_id'])
    if station_id not in configuration['station_mapping']['IMD']:
        raise ValueError('IMD station is not mapped to this city')
    if not str(p.get('station','')).strip():raise ValueError('IMD station name missing')
    day=str(p['dat']).removesuffix('Z')
    hour=float(p['utc'])
    if not hour.is_integer() or not 0<=hour<=23:raise ValueError('Unsupported IMD UTC observation hour')
    stamp=datetime.fromisoformat(day).replace(hour=int(hour),tzinfo=timezone.utc)
    lon,lat=feature['geometry']['coordinates'][:2]
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in [lat,lon]) or not -90<=lat<=90 or not -180<=lon<=180:
        raise ValueError('Invalid IMD station coordinates')
    ref=configuration['map_reference']
    if abs(lat-ref['latitude'])>1 or abs(lon-ref['longitude'])>1:raise ValueError('IMD station is outside configured city vicinity')
    readings={}
    for field,metric,unit,label,minimum,maximum in [
        ('dbtemp','temperature','degC','Temperature',-60,65),
        ('rh','humidity','%','Relative humidity',0,100),
        ('24hrlyrain','rainfall','mm','Rainfall · preceding 24 hours',0,3000),
        ('mslp','pressure','hPa','Sea-level pressure',800,1150)]:
        value=p.get(field)
        if value is None or str(value).strip().upper() in {'','NULL','NA','N/A','-999','-999.0'}:continue
        if isinstance(value,bool):raise ValueError('Invalid IMD reading')
        value=float(value)
        if not math.isfinite(value) or not minimum<=value<=maximum:continue
        readings[metric]={'value':value,'unit':unit,'label':label}
    if not readings:raise ValueError('No valid IMD readings')
    return {'source':'IMD','city_id':configuration['id'],'station_id':station_id,'station_name':p['station'],
            'observed_at':stamp.isoformat(),'provider_updated_at':p.get('update_time'),
            'coordinates':{'latitude':lat,'longitude':lon},'readings':readings,
            'kind':'observation','evidence_type':'station_observation','provider_url':REFERENCE,
            'data_url':WFS_URL,'attribution':'India Meteorological Department · public SYNOP map layer',
            'scope':'Individual weather station; not a citywide average',
            'freshness_limit_seconds':21600,'cadence':'SYNOP reports; observation time is UTC, not download time'}


async def fetch(configuration):
    if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':raise ValueError('Public provider requests disabled')
    gateway=os.getenv('CIVICFLUX_IMD_URL')
    if gateway:
        payload,stamp,error=await fetch_json(gateway)
        return {**payload,'fetched_at':stamp,'fetch_warning':error}
    payload,stamp,error=await fetch_json(WFS_URL,params={'service':'WFS','version':'1.0.0','request':'GetFeature',
        'typeName':'imd:synop_data_layer','outputFormat':'application/json'},ttl=300)
    if payload.get('type')!='FeatureCollection':raise ValueError('Unexpected IMD public layer response')
    stations=[]
    for feature in payload.get('features',[]):
        if str(feature.get('properties',{}).get('station_id')) not in configuration['station_mapping']['IMD']:continue
        try:stations.append(parse_station(feature,configuration))
        except (ValueError,KeyError,TypeError):continue
    if not stations:raise ValueError('Mapped IMD stations have no usable reports')
    preferred=configuration.get('preferred_imd_station')
    selected=next((s for s in stations if s['station_id']==preferred),max(stations,key=lambda s:s['observed_at']))
    return {**selected,'stations':stations,'fetched_at':stamp,'fetch_warning':error}
