"""Apply a session-derived PIN before any route or query executes."""
import json,re
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from backend.auth import resolve
from backend.scope import area
class JurisdictionMiddleware(BaseHTTPMiddleware):
 async def dispatch(self,request,call_next):
  path=request.url.path
  if not path.startswith('/api/') or path.startswith('/api/auth/') or path=='/api/health':return await call_next(request)
  if path.startswith('/api/civilian/'):
   response=await call_next(request)
   response.headers['Cache-Control']='no-store'
   return response
  session=resolve(request)
  if not session:
   if request.cookies.get('civicflux_session'):
    response=JSONResponse({'detail':'Admin session expired'},status_code=401)
    response.delete_cookie('civicflux_session')
    return response
   protected=path.startswith('/api/maps/geography/') or (path.startswith('/api/assessments/') and request.method=='POST' and path.split('/')[-1] in {'flood','cascade_risk','resource_optimization','intervention_outcomes','water_network'}) or (path.startswith('/api/predictions/') and path.split('/')[3] in {'flood','cascade_risk','resource_optimization','intervention_outcomes','water_network'})
   if protected:return JSONResponse({'detail':'Admin login required'},status_code=401)
   return await call_next(request)
  actor,scope=session;token=area.set(scope)
  try:
   if path.startswith('/api/predictions/') and not path.startswith('/api/predictions/outlook/'):
    raise HTTPException(403,'Research exports are not postal-area predictions')
   for key in ('pincode','postal_code'):
    if request.query_params.get(key) not in (None,'',scope['pincode']):raise HTTPException(403,'Outside your assigned area')
   if request.query_params.get('city_id') not in (None,scope['city_id']):raise HTTPException(403,'Outside your assigned area')
   match=re.match(r'/api/(?:civic/(?:weather|context|postal|planning)|municipal/(?:local|pincodes|locate|notice-archive)|maps/(?:air|geography)|predictions/outlook|cities)/([^/]+)',path)
   if match and match[1]!=scope['city_id']:raise HTTPException(403,'Outside your assigned area')
   if request.method in {'POST','PUT','PATCH'} and 'application/json' in request.headers.get('content-type',''):
    raw=await request.body()
    if len(raw)>1800000:raise HTTPException(413,'Request too large')
    try:body=json.loads(raw)
    except ValueError:body={}
    def check(item):
     if not isinstance(item,dict):return
     if item.get('city_id',scope['city_id'])!=scope['city_id']:raise HTTPException(403,'Outside your assigned area')
     for key in ('pincode','postal_code'):
      if item.get(key) not in (None,'',scope['pincode']):raise HTTPException(403,'Outside your assigned area')
     if isinstance(item.get('inputs'),dict):check(item['inputs'])
    check(body)
   return await call_next(request)
  except HTTPException as error:return JSONResponse({'detail':error.detail},status_code=error.status_code)
  finally:area.reset(token)
