"""Local public context and supervisor-only identity configuration."""
import asyncio
import os
import time
import json
from collections import defaultdict
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field,ConfigDict
import httpx
from backend.auth import admin
from backend.db.connection import connection
from backend.services.administration import supervisor,provision,profile,identity
from backend.services.municipal import local_context
from backend.services.civic_service import verify_pin,active
from backend.services.city_service import city
from backend.db import repository as repo
router=APIRouter(prefix='/api/municipal',tags=['PIN administration'])

@router.get('/pincodes/{city_id}')
def pins(city_id:str):
    city(city_id)
    with connection() as db:rows=[dict(r) for r in db.execute('SELECT * FROM pincodes WHERE city_id=? AND is_active=1 ORDER BY pincode',(city_id,))]
    from backend.scope import current
    if current():rows=[r for r in rows if r['pincode']==current()['pincode']]
    return {'city_id':city_id,'records':rows,'coverage':len(rows),'complete':False,'note':'Verified listed postal references only. PIN codes do not define municipal wards; unlisted areas require a reference update.'}

@router.get('/local/{city_id}')
def local(city_id:str,pincode:str|None=None):return local_context(city_id,pincode)

@router.get('/notice-archive/{city_id}')
def archived(city_id:str,pincode:str|None=None):
    city(city_id)
    if pincode:verify_pin(city_id,pincode)
    keys=('id','headline','description','area','publisher','valid_from','valid_until','source_url','pincode')
    from datetime import datetime,timezone
    def expired(n):
        try:return datetime.fromisoformat(n['valid_until'])<datetime.now(timezone.utc)
        except (ValueError,KeyError,TypeError):return False
    return [{k:n.get(k) for k in keys} for n in repo.all_records('civic_notice') if n['city_id']==city_id and expired(n) and (not n.get('pincode') or n.get('pincode')==pincode)]

class AreaAssignment(BaseModel):
    model_config=ConfigDict(extra='forbid')
    pincode:str=Field(pattern='^[0-9]{6}$')
    is_active:bool=True

@router.get('/administrators')
def administrators(actor:str=Depends(admin)):
    u=identity(actor)
    with connection() as db:return [dict(r) for r in db.execute('SELECT id,username,pincode,area_name,city_id,is_active,created_at,last_login_at FROM admins WHERE pincode=?',(u['pincode'],))]

@router.post('/administrators')
def add_admin(body:AreaAssignment,actor:str=Depends(admin)):
    u=identity(actor)
    if body.pincode!=u['pincode']:raise HTTPException(403,'Outside your assigned area')
    with connection() as db:
        db.execute('UPDATE admins SET is_active=? WHERE pincode=?',(int(body.is_active),u['pincode']))
        if not body.is_active:db.execute('DELETE FROM sessions WHERE actor=?',(actor,))
    return {'pincode':u['pincode'],'is_active':body.is_active}

class Location(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    latitude:float=Field(ge=-90,le=90)
    longitude:float=Field(ge=-180,le=180)

_geo_lock=asyncio.Lock();_geo_clock=0.0;_geo_cache={}
@router.post('/locate/{city_id}')
async def locate(city_id:str,body:Location):
    latitude,longitude=body.latitude,body.longitude
    global _geo_clock
    c=city(city_id);ref=c['map_reference']
    base={'city_id':city_id,'pincode':None,'status':'manual_selection_required','source':'OpenStreetMap Nominatim','attribution':'© OpenStreetMap contributors · ODbL','note':'A geocoder suggestion is not a postal boundary or verified municipal jurisdiction. Confirm or correct the PIN manually.'}
    if abs(latitude-ref['latitude'])>.6 or abs(longitude-ref['longitude'])>.6:return {**base,'reason':'Location is outside this city vicinity. Select the city and PIN manually.'}
    if os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':return {**base,'reason':'Location lookup is unavailable; choose a PIN manually.'}
    key=(city_id,round(latitude,4),round(longitude,4))
    async with _geo_lock:
        cached=_geo_cache.get(key)
        if cached and time.monotonic()-cached[0]<3600:return cached[1]
        delay=max(0,1.05-(time.monotonic()-_geo_clock))
        if delay:await asyncio.sleep(delay)
        _geo_clock=time.monotonic()
        try:
            endpoint=os.getenv('CIVICFLUX_GEOCODER_URL','https://nominatim.openstreetmap.org/reverse')
            if not endpoint.startswith('https://'):raise ValueError('HTTPS geocoder required')
            async with httpx.AsyncClient(timeout=10,headers={'User-Agent':'CivicFlux-locality/1.0 (https://github.com/jiyyahooda/civicflux)'}) as client:
                response=await client.get(endpoint,params={'format':'jsonv2','lat':key[1],'lon':key[2],'zoom':18,'addressdetails':1});response.raise_for_status();payload=response.json()
            candidate=payload.get('address',{}).get('postcode','')
            try:verify_pin(city_id,candidate)
            except HTTPException:return {**base,'reason':'No unambiguous listed PIN was returned. Choose it manually.'}
            result={**base,'status':'suggestion','pincode':candidate,'locality':payload.get('address',{}).get('suburb','')}
            if len(_geo_cache)>200:_geo_cache.clear()
            _geo_cache[key]=(time.monotonic(),result);return result
        except (httpx.HTTPError,ValueError,TypeError):return {**base,'reason':'Location lookup failed; manual selection remains available.'}
