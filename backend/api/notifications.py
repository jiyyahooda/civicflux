"""Polling-only, source-timestamped alerts. No push service or private email exposure."""
import asyncio,hashlib,math,os,re
from datetime import datetime,timezone
from fastapi import APIRouter,Query
from backend.integrations.weather import weather
from backend.services.observation_service import observations
from backend.services.civic_service import context
from backend.services.city_service import city
from backend.db import repository
router=APIRouter(prefix='/api/civic',tags=['In-app notifications'])
def threshold(name,default):
    try:
        value=float(os.getenv(name,str(default)))
        return value if math.isfinite(value) and value>=0 else default
    except ValueError:return default
def build_notifications(cid,weather_data,observation_data,civic,tracked):
    result=[]
    def add(key,title,detail,source,stamp):
        if not isinstance(stamp,str) or not stamp:return
        source=source if isinstance(source,str) else "CivicFlux source unavailable"
        result.append({'id':hashlib.sha256((cid+':'+key+':'+stamp).encode()).hexdigest(),'city_id':cid,'title':title,'detail':detail,'source':source,'event_time':stamp})
    if weather_data.get('city_id')==cid and weather_data.get('status')=='available' and weather_data.get('current'):
        c=weather_data['current'];stamp=weather_data.get('observed_at');rain=threshold('CIVICFLUX_ALERT_RAIN_MM',10);heat=threshold('CIVICFLUX_ALERT_TEMP_C',40)
        if c['precipitation']>=rain:add('rain','Rainfall threshold reached',f"Provider grid reports {c['precipitation']:g} mm; configured threshold {rain:g} mm. This is not neighbourhood coverage.",weather_data['source_url'],stamp)
        if c['temperature_2m']>=heat:add('heat','Temperature threshold reached',f"Provider grid reports {c['temperature_2m']:g} °C; configured threshold {heat:g} °C.",weather_data['source_url'],stamp)
    if observation_data.get('city_id')==cid:
        for f in observation_data.get('feeds',[]):
            value=(f.get('readings') or {}).get('us_aqi',{}).get('value');limit=threshold('CIVICFLUX_ALERT_US_AQI',151)
            if f.get('status') in ('fresh','available') and isinstance(value,(int,float)) and math.isfinite(value) and value>=limit:
                add('air:'+f['source'],'Modelled air-quality threshold reached',f'US AQI {value:g} from {f["source"]}; threshold {limit:g}. Modelled regional grid, not the CPCB index.',f.get('provider_url','https://open-meteo.com/en/docs/air-quality-api'),f.get('observed_at'))
    if civic.get('city_id')==cid:
        for n in civic.get('notices',[]):add('notice:'+n['id'],n['headline'],n['description'],n['source_url'],n.get('valid_from') or n.get('created'))
    for report in tracked:
        if report.get('city_id')==cid:
            add('report:'+report['id']+':'+report['status'],'Report '+report['status'].replace('_',' '),str(report.get('title') or 'CivicFlux report')+' · '+str(report.get('public_reply') or 'Check Track your report for the latest public response.'),'CivicFlux report tracking',report.get('updated_at') or report['created'])
    return sorted({r['id']:r for r in result}.values(),key=lambda r:r['event_time'],reverse=True)[:100]
@router.get('/notifications/{identifier}')
async def notifications(identifier:str,tracking_ids:str=Query('',max_length=2000),pincode:str|None=Query(None,pattern=r'^[0-9]{6}$')):
    city(identifier)
    from backend.services.civic_service import verify_pin
    from backend.db.connection import connection
    if not pincode:return {'city_id':identifier,'pincode':None,'items':[],'checked_at':datetime.now(timezone.utc).isoformat(),'limitations':'Select your postal area for relevant notifications.','unavailable_sources':[]}
    verify_pin(identifier,pincode)
    with connection() as db:point=db.execute('SELECT latitude,longitude FROM admins WHERE city_id=? AND pincode=?',(identifier,pincode)).fetchone()
    reference={'latitude':point['latitude'],'longitude':point['longitude']} if point and point['latitude'] is not None else None
    async def safe(fn):
        try:return await fn(identifier,reference=reference,pincode=pincode) if reference else {}
        except Exception:return {}
    w,o=await asyncio.gather(safe(weather),safe(observations));c=context(identifier);c={**c,'notices':[n for n in c.get('notices',[]) if n.get('pincode')==pincode]};tracked=[]
    for id in list(dict.fromkeys(tracking_ids.split(',')))[:20]:
        if not re.fullmatch(r'[0-9a-fA-F-]{36}',id):continue
        try:
            report=repository.get('complaint',id)
            if report.get('postal_code')==pincode:tracked.append(report)
        except Exception:continue
    return {'city_id':identifier,'pincode':pincode,'items':[{**n,'id':hashlib.sha256((pincode+n['id']).encode()).hexdigest(),'pincode':pincode} for n in build_notifications(identifier,w,o,c,tracked)],'checked_at':datetime.now(timezone.utc).isoformat(),'poll_seconds':60,
      'limitations':'Checked while this page is open. Polling and source refresh intervals can delay alerts; no background or browser push delivery.',
      'unavailable_sources':(['weather'] if not (w.get('current') and w.get('status')=='available') else [])+(['air quality'] if not any(f.get('readings') for f in o.get('feeds',[]) if f.get('source')=='CAMS' and f.get('status') in ('fresh','available')) else [])}
