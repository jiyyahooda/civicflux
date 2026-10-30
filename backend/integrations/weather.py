"""Open-Meteo weather at the requested city grid, separate from saved ML."""
import math, os
from datetime import datetime, timezone, timedelta
from backend.integrations.source_http import fetch_json
from backend.services.city_service import city
URL='https://api.open-meteo.com/v1/forecast'
CURRENT={'temperature_2m':'°C','apparent_temperature':'°C','relative_humidity_2m':'%','precipitation':'mm','wind_speed_10m':'km/h','weather_code':'wmo code'}
DAILY=['temperature_2m_max','temperature_2m_min','precipitation_sum','precipitation_probability_max','weather_code']

async def weather(identifier):
 c=city(identifier); ref=c['map_reference']
 base={'pincode':c.get('pincode'),'city_id':identifier,'provider':'Open-Meteo Weather','source_url':'https://open-meteo.com/en/docs', 'attribution':'Weather data by Open-Meteo.com · CC BY 4.0','checked_at':datetime.now(timezone.utc).isoformat(),'resolution_note':'One provider grid near the city reference; no neighbourhood rainfall coverage is implied.'}
 try:
  if not ref:raise ValueError('Postal reference coordinates unavailable')
  if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':raise ValueError('Provider requests are disabled')
  p,stamp,warning=await fetch_json(URL,params={'latitude':ref['latitude'],'longitude':ref['longitude'],'current':','.join(CURRENT),'daily':','.join(DAILY),'hourly':'precipitation,temperature_2m','forecast_days':7,'timezone':c['timezone']},ttl=900)
  if not (p.get('timezone')==c['timezone'] or {p.get('timezone'),c['timezone']}=={'Asia/Kolkata','Asia/Calcutta'}) or abs(p['latitude']-ref['latitude'])>1 or abs(p['longitude']-ref['longitude'])>1:raise ValueError('Weather location could not be verified')
  if any(p.get('current_units',{}).get(k)!=u for k,u in CURRENT.items()):raise ValueError('Unexpected weather units')
  current=p['current']
  if any(not isinstance(current.get(k),(float,int)) or isinstance(current[k],bool) or not math.isfinite(current[k]) for k in CURRENT):raise ValueError('Incomplete current weather')
  daily=p['daily']; rows=[]
  expected={'temperature_2m_max':'°C','temperature_2m_min':'°C','precipitation_sum':'mm','precipitation_probability_max':'%','weather_code':'wmo code'}
  if any(p.get('daily_units',{}).get(k)!=v for k,v in expected.items()):raise ValueError('Unexpected daily units')
  today=datetime.now(__import__('zoneinfo').ZoneInfo(c['timezone'])).date()
  for i,t in enumerate(daily['time']):
   row={'date':t,**{k:daily[k][i] for k in DAILY}}
   if not today<=datetime.fromisoformat(t).date()<today+timedelta(days=7):continue
   if all(isinstance(row[k],(int,float)) and not isinstance(row[k],bool) and math.isfinite(row[k]) for k in DAILY) and 0<=row['precipitation_probability_max']<=100 and row['precipitation_sum']>=0 and row['temperature_2m_min']<=row['temperature_2m_max']:rows.append(row)
  if not rows:raise ValueError('No current forecast days')
  hourly=p.get('hourly',{}); hours=[{'time':t,'rain_mm':hourly['precipitation'][i],'temperature':hourly['temperature_2m'][i]} for i,t in enumerate(hourly.get('time',[])) if hourly['precipitation'][i] is not None and hourly['temperature_2m'][i] is not None]
  observed=datetime.fromisoformat(current['time']).replace(tzinfo=__import__('zoneinfo').ZoneInfo(c['timezone']))
  age=(datetime.now(timezone.utc)-observed).total_seconds()
  return {**base,'status':'stale' if warning or age>7200 or age< -900 else 'available','current':current,'observed_at':observed.isoformat(),'days':rows,'hourly':hours[:48],'coordinates':{'latitude':p['latitude'],'longitude':p['longitude']},'warning':'Provider cache may be stale' if warning else None,'fetched_at':stamp}
 except Exception as error:
  reason=str(error) if isinstance(error,ValueError) and str(error) in {'Postal reference coordinates unavailable','Provider requests are disabled','Weather location could not be verified','Unexpected weather units','Incomplete current weather','Unexpected daily units','No current forecast days'} else 'Weather provider could not return a valid response; retry or check CIVICFLUX_PUBLIC_FEEDS and network access.'
  return {**base,'status':'unavailable','current':None,'days':[],'hourly':[],'reason':reason}
