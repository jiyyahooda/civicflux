"""Live WAQI station data. No persistent cache, raw concentrations or key exposure."""
import math,os
from datetime import datetime,timezone
import httpx
from backend.services.city_service import city
FEEDS={'delhi':'delhi','chennai':'chennai','chandigarh':'chandigarh'}

def number(value):
 try:value=float(value)
 except (ValueError,TypeError):return None
 return value if math.isfinite(value) and 0<=value<=1000 else None

def normalize_stations(rows):
 result=[];seen=set()
 for row in rows:
  if not isinstance(row,dict):continue
  try:lat,lon=float(row['lat']),float(row['lon']);uid=int(row['uid'])
  except (KeyError,ValueError,TypeError):continue
  value=number(row.get('aqi'));station=row.get('station') if isinstance(row.get('station'),dict) else {}
  if value is None or not (-90<=lat<=90 and -180<=lon<=180) or uid in seen:continue
  seen.add(uid)
  result.append({'id':uid,'name':str(station.get('name') or 'WAQI station')[:200],'latitude':lat,'longitude':lon,'aqi':value,'observed_at':str(station.get('time') or 'Provider timestamp unavailable'),'source_url':'https://aqicn.org/station/@'+str(uid)})
 return result

async def air_quality(identifier):
 config=city(identifier);ref=config['map_reference'];now=datetime.now(timezone.utc).isoformat()
 base={'city_id':identifier,'city_name':config['name'],'fetched_at':now,'stations':[],'standard':'US EPA AQI via WAQI; not Indian NAQI or pollutant concentration','map_url':'https://aqicn.org/map/'+FEEDS[identifier]+'/','provider':'World Air Quality Index project','attributions':[],'surface_note':'Colour shading is an illustrative interpolation near reporting stations, not measured neighbourhood boundaries.','coverage_note':'Selected city area and nearby stations; no administrative-boundary claim.'}
 token=os.getenv('WAQI_API_TOKEN','').strip()
 if not token:return {**base,'status':'unavailable','reason':'WAQI token is not configured on the server.'}
 if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':return {**base,'status':'unavailable','reason':'Live provider access is disabled in this environment.'}
 bounds=f"{ref['latitude']-.25},{ref['longitude']-.35},{ref['latitude']+.25},{ref['longitude']+.35}"
 try:
  import asyncio
  async with httpx.AsyncClient(timeout=12,follow_redirects=False) as client:
   feed,points=await asyncio.gather(client.get('https://api.waqi.info/feed/'+FEEDS[identifier]+'/',params={'token':token}),client.get('https://api.waqi.info/map/bounds/',params={'token':token,'latlng':bounds}))
  if feed.status_code!=200 or points.status_code!=200:raise ValueError()
  feed=feed.json();points=points.json()
  if not isinstance(feed,dict) or not isinstance(points,dict):raise ValueError()
  if feed.get('status')!='ok' or points.get('status')!='ok':raise ValueError()
  data=feed.get('data') or {}
  if not isinstance(data,dict) or not isinstance(points.get('data'),list):raise ValueError()
  stations=normalize_stations(points['data'])
  credits=[{'name':str(a.get('name',''))[:200],'url':str(a.get('url',''))} for a in data.get('attributions',[]) if isinstance(a,dict) and (str(a.get('url','')).startswith('https://') or str(a.get('url','')).startswith('http://'))]
  return {**base,'status':'available' if stations else 'unavailable','reason':None if stations else 'No numeric WAQI station readings are available in this area.','stations':stations,'city_aqi':number(data.get('aqi')),'city_station':str((data.get('city') or {}).get('name','')),'observed_at':(data.get('time') or {}).get('iso') or (data.get('time') or {}).get('s'),'dominant_pollutant':data.get('dominentpol'),'attributions':credits}
 except (httpx.HTTPError,ValueError,TypeError,KeyError):
  return {**base,'status':'unavailable','reason':'WAQI is unavailable or rejected access. Check the server token and provider availability.'}
