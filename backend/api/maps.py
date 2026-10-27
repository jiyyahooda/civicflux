"""Read-only map references and explicitly synthetic map states."""
import json,os
from pathlib import Path
from fastapi import APIRouter,Response,HTTPException,Query
from pydantic import BaseModel,Field,ConfigDict
from backend.integrations.waqi import air_quality
from backend.services.city_service import city
from project_paths import PROJECT_ROOT
router=APIRouter(prefix='/api/maps',tags=['geographic display and simulated scenarios'])

@router.get('/air/{identifier}')
async def air(identifier:str,response:Response):
 response.headers['Cache-Control']='no-store'
 return await air_quality(identifier)

@router.get('/geography/{identifier}')
def geography(identifier:str):
 city(identifier)
 if identifier!='delhi':return {'city_id':identifier,'status':'unavailable','reason':'The named scenario geography is available for Delhi only.'}
 return json.loads((PROJECT_ROOT/'data/geography/delhi_demo.json').read_text(encoding='utf-8'))

@router.get('/geography/{identifier}/download')
def download_geography(identifier:str,rain_mm:float=Query(60,ge=0,le=200),blockage:float=Query(.35,ge=0,le=1),volume:int=Query(900,ge=0,le=100000),capacity:int=Query(1200,gt=0,le=100000),outages:str=Query('',max_length=1000)):
 body=geography(identifier)
 if body.get('status')!='available':raise HTTPException(404,'Scenario geography unavailable')
 ids=outages.split(',') if outages else body['default_outages']
 if any(i not in {a['id'] for a in body['assets']} for i in ids):raise HTTPException(422,'Unknown simulated asset')
 body.update(assumptions={'rain_mm':rain_mm,'blockage':blockage,'vehicles_per_hour':volume,'capacity_per_hour':capacity},declared_outages=ids,warning='Simulated positions, links and conditions; not surveyed infrastructure or live incident records.')
 return Response(json.dumps(body,indent=2,allow_nan=False),media_type='application/json',headers={'Content-Disposition':'attachment; filename="civicflux-delhi-simulated-scenario.json"'})

class TrafficInput(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 vehicles_per_hour:float=Field(ge=0,le=100000)
 assumed_capacity:float=Field(gt=0,le=100000)

@router.post('/traffic-interpretation')
def traffic_interpretation(body:TrafficInput):
 ratio=body.vehicles_per_hour/body.assumed_capacity
 category='Low' if ratio<.5 else 'Moderate' if ratio<.8 else 'High' if ratio<=1 else 'Over assumed capacity'
 return {'volume_capacity_ratio':ratio,'category':category,'basis':'Illustrative capacity rule, not an ML congestion prediction','explanation':f'{body.vehicles_per_hour:g} vehicles/hour divided by {body.assumed_capacity:g} assumed vehicles/hour gives {ratio:.2f}.','thresholds':{'low':'below 0.50','moderate':'0.50 to below 0.80','high':'0.80 to 1.00','over_capacity':'above 1.00'},'limitations':'Volume alone does not establish speed, queues or travel time. Capacity and cutoffs are editable scenario assumptions.'}

@router.get('/weather-configuration')
def weather_configuration():return {'precipitation_tiles_configured':bool(os.getenv('OPENWEATHERMAP_API_KEY',''))}

@router.get('/rain-tiles/{z}/{x}/{y}.png')
async def rain_tile(z:int,x:int,y:int):
 from fastapi.responses import Response
 import httpx
 if not 0<=z<=18 or not 0<=x<2**z or not 0<=y<2**z:raise HTTPException(422,'Invalid map tile')
 token=os.getenv('OPENWEATHERMAP_API_KEY','').strip()
 if not token or os.getenv('CIVICFLUX_PUBLIC_FEEDS','1')!='1':raise HTTPException(503,'OpenWeather precipitation tiles are not configured')
 try:
  async with httpx.AsyncClient(timeout=10) as client:r=await client.get(f'https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png',params={'appid':token})
  if r.status_code!=200 or 'image/png' not in r.headers.get('content-type',''):raise ValueError()
  return Response(r.content,media_type='image/png',headers={'Cache-Control':'no-store'})
 except (httpx.HTTPError,ValueError):raise HTTPException(503,'Precipitation tile provider is unavailable')
