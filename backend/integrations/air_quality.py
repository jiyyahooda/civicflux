"""CAMS global gridded estimates via Open-Meteo; never called CPCB readings."""
import os
import math
from datetime import datetime,timezone
from .source_http import fetch_json

URL='https://air-quality-api.open-meteo.com/v1/air-quality'


def parse(payload,configuration):
    location=configuration['map_reference'];current=payload['current'];units=payload['current_units']
    lat,lon=float(payload['latitude']),float(payload['longitude'])
    if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat-location['latitude'])>1 or abs(lon-location['longitude'])>1:
        raise ValueError('CAMS grid does not match the requested city vicinity')
    if units.get('time')!='unixtime':raise ValueError('Unexpected CAMS timestamp unit')
    stamp=datetime.fromtimestamp(current['time'],tz=timezone.utc)
    readings={}
    for source,target,label,unit,expected in [('pm2_5','pm25','PM2.5 · CAMS estimate','ug/m3','μg/m³'),
        ('pm10','pm10','PM10 · CAMS estimate','ug/m3','μg/m³'),('us_aqi','us_aqi','US AQI · CAMS estimate','US AQI','USAQI')]:
        value=current.get(source)
        if value is None:continue
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise ValueError('Invalid CAMS value')
        if units.get(source)!=expected:raise ValueError('Unexpected CAMS unit')
        readings[target]={'value':value,'unit':unit,'label':label}
    if not readings:raise ValueError('CAMS returned no current estimates')
    hourly=payload.get('hourly',{});series=[]
    if hourly.get('time'):
        hourly_units=payload.get('hourly_units',{})
        if hourly_units.get('time')!='unixtime' or any(hourly_units.get(k)!=v for k,v in {'pm2_5':'μg/m³','pm10':'μg/m³','us_aqi':'USAQI'}.items()):
            raise ValueError('Unexpected CAMS hourly unit')
    for index,t in enumerate(hourly.get('time',[])):
        values={name:hourly[name][index] for name in ['pm2_5','pm10','us_aqi'] if name in hourly}
        if any(v is None or isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in values.values()):continue
        series.append({'time':datetime.fromtimestamp(t,tz=timezone.utc).isoformat(),**values,'is_future':t>current['time']})
    return {'source':'CAMS','provider_name':'CAMS via Open-Meteo','city_id':configuration['id'],'station_id':None,
        'station_name':'CAMS global grid · not a monitoring station','observed_at':stamp.isoformat(),'valid_at':stamp.isoformat(),
        'coordinates':{'latitude':lat,'longitude':lon},'readings':readings,'series':series,
        'kind':'model_estimate','evidence_type':'model_estimate','freshness_limit_seconds':10800,
        'provider_url':'https://open-meteo.com/en/docs/air-quality-api','data_url':URL,
        'attribution':'Copernicus Atmosphere Monitoring Service (CAMS) global composition forecasts via Open-Meteo · CC BY 4.0',
        'scope':'Approx. 45 km global atmospheric model grid; not a street-level measurement',
        'index_standard':'US EPA AQI; not CPCB / Indian AQI',
        'limitations':['These are model estimates, not CPCB monitoring observations.',
                        'Valid time is not the underlying model issuance time; issuance is not exposed here.',
                        'CAMS global native resolution is approximately 45 km; no health or intervention decision is automated.']}


async def fetch(configuration):
    if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':raise ValueError('Public provider requests disabled')
    location=configuration['map_reference']
    payload,stamp,error=await fetch_json(URL,params={'latitude':location['latitude'],'longitude':location['longitude'],
        'current':'pm2_5,pm10,us_aqi','hourly':'pm2_5,pm10,us_aqi','domains':'cams_global','timezone':'UTC',
        'forecast_days':1,'timeformat':'unixtime'},ttl=900)
    return {**parse(payload,configuration),'fetched_at':stamp,'fetch_warning':error}
