"""Current external numerical weather outlook, separate from fitted ML contracts."""
import math
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.integrations.source_http import fetch_json
from backend.services.city_service import city

URL='https://api.open-meteo.com/v1/forecast'
FIELDS={'temperature_2m_max':'°C','temperature_2m_min':'°C','precipitation_sum':'mm','wind_speed_10m_max':'km/h'}

def parse(payload, configuration, today):
    ref=configuration['map_reference']
    if abs(float(payload['latitude'])-ref['latitude'])>1 or abs(float(payload['longitude'])-ref['longitude'])>1:
        raise ValueError('Forecast grid does not match the selected city')
    if payload.get('timezone')!=configuration['timezone']:raise ValueError('Unexpected forecast timezone')
    daily=payload['daily']; units=payload['daily_units']
    for name,unit in FIELDS.items():
        if units.get(name)!=unit:raise ValueError('Forecast unit mismatch')
        if len(daily[name])!=len(daily['time']):raise ValueError('Incomplete daily forecast arrays')
    rows=[]
    for i,date in enumerate(daily['time']):
        day=datetime.strptime(date,'%Y-%m-%d').date()
        if not today<day<=today+timedelta(days=14):continue
        values={k:daily[k][i] for k in FIELDS}
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in values.values()):continue
        if values['precipitation_sum']<0 or values['wind_speed_10m_max']<0 or values['temperature_2m_min']>values['temperature_2m_max']:continue
        rows.append({'date':date,**values})
    if not rows:raise ValueError('No upcoming forecast dates returned')
    dates=[r['date'] for r in rows]
    if dates!=sorted(set(dates)):raise ValueError('Invalid forecast date sequence')
    return rows

async def outlook(identifier):
    configuration=city(identifier)
    now=datetime.now(ZoneInfo(configuration['timezone']))
    base={'city_id':identifier,'kind':'weather_forecast','provider':'Open-Meteo numerical weather forecast',
          'attribution':'Weather data by Open-Meteo.com · CC BY 4.0','timezone':configuration['timezone'],
          'requested_days':14,'checked_at':now.isoformat(),'units':FIELDS,'uncertainty':None}
    try:
        if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':raise ValueError('Public provider requests disabled')
        ref=configuration['map_reference']
        payload,stamp,warning=await fetch_json(URL,params={'latitude':ref['latitude'],'longitude':ref['longitude'],
            'daily':','.join(FIELDS),'forecast_days':15,'timezone':configuration['timezone']},ttl=1800)
        rows=parse(payload,configuration,now.date())
        return {**base,'status':'stale' if warning else 'available','fetched_at':stamp,'warning':warning,
                'rows':rows,'available_days':len(rows),'complete':len(rows)==14}
    except (ValueError,KeyError,TypeError,OverflowError) as error:
        return {**base,'status':'unavailable','rows':[],'available_days':0,'complete':False,
                'reason':str(error) if isinstance(error,ValueError) else 'Invalid provider forecast response'}
