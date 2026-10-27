"""Key-based CPCB OGD connector; no inferred AQI or undocumented units."""
import os
import math
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from .source_http import fetch_json

RESOURCE='https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69'
REFERENCE='https://www.data.gov.in/resource/real-time-air-quality-index-various-locations'


def identity(value):return re.sub('[^a-z0-9]','',str(value).lower())


def parse(payload,configuration):
    stations={};ref=configuration['map_reference']
    for row in payload.get('records',[]):
        if identity(row.get('city'))!=identity(configuration['name']) or identity(row.get('state'))!=identity(configuration['source_state']):continue
        if row.get('country')!='India':continue
        lat,lon=float(row['latitude']),float(row['longitude'])
        if not all(math.isfinite(v) for v in [lat,lon]) or abs(lat-ref['latitude'])>1 or abs(lon-ref['longitude'])>1:continue
        station=str(row['station']).strip()
        if not station:continue
        stamp=datetime.strptime(row['last_update'],'%d-%m-%Y %H:%M:%S').replace(tzinfo=ZoneInfo('Asia/Kolkata')).isoformat()
        value=row.get('pollutant_avg')
        if value is None or str(value).upper() in {'NA','N/A','NULL',''}:continue
        value=float(value)
        if not math.isfinite(value) or value<0:continue
        pollutant=str(row['pollutant_id'])
        key=(station,stamp)
        item=stations.setdefault(key,{'source':'CPCB','city_id':configuration['id'],'station_id':station,'station_name':station,
            'station_mapping_method':'provider city/state identity and coordinates','coordinates':{'latitude':lat,'longitude':lon},
            'observed_at':stamp,'readings':{},'provider_url':REFERENCE,'data_url':RESOURCE,
            'attribution':'Central Pollution Control Board via Open Government Data Platform India',
            'scope':'Individual CPCB station report','freshness_limit_seconds':10800,
            'limitations':['Publisher pollutant_avg unit is not explicit in this connector; no PM concentration or overall AQI is inferred.',
                'Source last_update interpreted as Asia/Kolkata; original timestamp lacks an explicit timezone.']})
        item['readings']['reported_'+pollutant]={'value':value,'unit':'publisher value; unit unverified','label':pollutant+' · publisher report'}
    if not stations:raise ValueError('CPCB returned no usable stations for the verified city/state')
    selected=sorted(stations.values(),key=lambda s:(s['observed_at'],s['station_id']),reverse=True)[0]
    return {**selected,'stations':list(stations.values()),'station_selection':'Latest available station report; deterministic station-name tie-break',
        'pagination_complete':int(payload.get('total',len(payload.get('records',[]))))<=len(payload.get('records',[]))}


async def fetch(configuration):
    if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':raise ValueError('Public provider requests disabled')
    gateway=os.getenv('CIVICFLUX_CPCB_URL')
    if gateway:
        payload,stamp,error=await fetch_json(gateway)
        return {**payload,'fetched_at':stamp,'fetch_warning':error}
    key=os.getenv('DATA_GOV_IN_API_KEY','').strip()
    if not key:raise ValueError('Official CPCB feed needs your data.gov.in API key. Set DATA_GOV_IN_API_KEY in the local .env file; CAMS estimates are available separately.')
    payload,stamp,error=await fetch_json(RESOURCE,params={'api-key':key,'format':'json','limit':1000,
        'filters[city]':configuration['name']},ttl=900)
    return {**parse(payload,configuration),'fetched_at':stamp,'fetch_warning':error}
