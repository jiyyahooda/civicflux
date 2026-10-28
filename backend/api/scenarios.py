import math
from typing import Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel,Field,ConfigDict,field_validator
from backend.auth import admin
from backend.services.administration import visible,require_record,require_scope
from backend.db import repository as repo
from backend.services.scenario_service import execute
from backend.graph import dependencies
router=APIRouter(prefix='/api/scenarios',tags=['synthetic scenarios'])
class Flood(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    rain_mm:float=Field(default=60,ge=0,le=200)
    duration_h:float=Field(default=6,ge=1,le=12)
    area_m2:float=Field(default=50000,ge=10000,le=100000)
    runoff_coefficient:float=Field(default=.7,ge=.3,le=.95)
    drain_mm_h:float=Field(default=3,ge=.2,le=8)
    blockage:float=Field(default=.5,ge=0,le=.9)
    ponding_fraction:float=Field(default=.1,ge=.03,le=.2)
    initial_storage_mm:float=Field(default=0,ge=0,le=2)
class Resources(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    budget:int=Field(default=50000,ge=0,le=10000000,strict=True)
    pumps:int=Field(default=4,ge=0,le=1000,strict=True)
    crew_hours:dict[str,float]=Field(default_factory=lambda:{'water':24,'road':24,'drain':24})
    @field_validator('crew_hours')
    @classmethod
    def valid_hours(cls,v):
        if any(not math.isfinite(x) or not 0<=x<=10000 for x in v.values()): raise ValueError('Invalid crew hours')
        return v
class Scenario(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    name:str=Field(default='Monsoon stress test',min_length=3,max_length=100)
    city_id:str='delhi'
    pincode:str|None=None
    flood_engine:Literal['mass_balance','trained_surrogate']='mass_balance'
    flood:Flood=Field(default_factory=Flood)
    initial:list[str]=Field(default_factory=lambda:['pump_0'],max_length=40)
    load:float=Field(default=1.1,ge=.5,le=1.5)
    resources:Resources=Field(default_factory=Resources)
    weights:dict[str,float]|None=None
@router.get('')
def index(actor:str=Depends(admin)): return [s for s in repo.all_records('scenario') if visible(actor,s)]
@router.get('/graph')
def graph(actor:str=Depends(admin)): return dependencies()
@router.get('/defaults')
def defaults(actor:str=Depends(admin)):
    from backend.scope import current
    scope=current()
    return Scenario(city_id=scope['city_id'],pincode=scope['pincode']).model_dump() if scope else Scenario().model_dump()
@router.get('/{identifier}')
def detail(identifier:str,actor:str=Depends(admin)):
    item=repo.get('scenario',identifier);require_record(actor,item);return item
@router.post('')
def run(body:Scenario,actor:str=Depends(admin)):
    from backend.services.city_service import city
    from backend.scope import current
    if current():body=body.model_copy(update={'pincode':current()['pincode']})
    city(body.city_id);require_scope(actor,body.city_id,body.pincode)
    if body.pincode:
        from backend.services.civic_service import verify_pin
        verify_pin(body.city_id,body.pincode)
    return execute(body,actor)
