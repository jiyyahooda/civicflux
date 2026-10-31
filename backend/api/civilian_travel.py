"""Match only dated, official-source notices to the submitted route geometry."""
import math
from urllib.parse import urlsplit
from fastapi import APIRouter,Request
from pydantic import Field
from backend.api.civilian import Strict,Point
from backend.services.civic_service import context,SOURCES,active
from backend.services.city_service import city
from backend.db.repository import now
router=APIRouter(prefix='/api/civilian',tags=['Travel advisories'])
class RouteCheck(Strict):
 city_id:str=Field(max_length=30)
 path:list[Point]=Field(min_length=2,max_length=10000)
def near_route(point,path,radius=500):
 """Local equirectangular point-to-segment distance in metres, not vertex matching."""
 lat,lon=point;scale=math.cos(math.radians(lat));best=float('inf')
 for a,b in zip(path,path[1:]):
  ax=(a.longitude-lon)*111320*scale;ay=(a.latitude-lat)*111320;bx=(b.longitude-lon)*111320*scale;by=(b.latitude-lat)*111320
  dx,dy=bx-ax,by-ay;t=max(0,min(1,-(ax*dx+ay*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
  best=min(best,math.hypot(ax+t*dx,ay+t*dy))
 return best<=radius
@router.post('/travel/check')
def check(body:RouteCheck,request:Request):
 from backend.auth import same_origin
 same_origin(request)
 city(body.city_id);allowed={urlsplit(s).hostname for s in SOURCES[body.city_id].values()};matched=[];unmapped=[]
 for notice in context(body.city_id)['notices']:
  if not active(notice):continue
  source=urlsplit(notice.get('source_url',''))
  if source.scheme!='https' or source.hostname not in allowed or source.username or source.password:continue
  item={k:notice.get(k) for k in ('id','headline','description','source_url','valid_from','valid_until','locality')}
  coords=notice.get('coordinates');point=None
  if isinstance(coords,dict):
   lat,lon=coords.get('latitude'),coords.get('longitude')
   if all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in (lat,lon)) and -90<=lat<=90 and -180<=lon<=180:point=(lat,lon)
  if point:
   if near_route(point,body.path):matched.append({**item,'match':'Within 500 m of route; notice location is approximate.'})
  else:unmapped.append(item)
 return {'checked_at':now(),'route_notices':matched,'unmapped_city_notices':unmapped,'sources':SOURCES[body.city_id],
 'coverage':'Approved, unexpired official-source imports only. No automatic police or municipal incident feed is connected. Absence of a matched notice does not mean a route is clear.',
 'waterlogging_status':'unknown','waterlogging_reason':'No complete live official road-level waterlogging feed is configured. Consult the linked official notices.',
 'model_status':'not_applicable','model_reason':'Saved rainfall, flood and traffic artifacts are historical or simulated and have no validated mapping to this route. They cannot provide a live route safety score.'}
