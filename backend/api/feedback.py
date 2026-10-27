from datetime import datetime
from typing import Literal
from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field,model_validator
from backend.auth import admin
from backend.db import repository as repo
from backend.services.feedback_service import review,verification
router=APIRouter(prefix='/api',tags=['human review and community'])
class Review(BaseModel):
    decision:Literal['pending','defer','reject','approve']
    note:str=Field(min_length=3,max_length=2000)
class Verification(BaseModel):
    verifier:str=Field(min_length=3,max_length=100)
    evidence_ref:str=Field(min_length=3,max_length=500)
    success:bool
    completion_time:datetime
    verification_time:datetime
    note:str=Field(min_length=3,max_length=2000)
    @model_validator(mode='after')
    def chronology(self):
        from datetime import timezone
        if self.completion_time.tzinfo is None or self.verification_time.tzinfo is None: raise ValueError('Timezone-aware timestamps required')
        if self.verification_time<self.completion_time or self.verification_time>datetime.now(timezone.utc): raise ValueError('Invalid outcome chronology')
        return self
    def model_dump(self,**kwargs): return super().model_dump(mode='json',**kwargs)
class Complaint(BaseModel):
    city_id:str
    locality:Literal['north','north_west','south','south_west','south_east','north_east','east','west','central']='central'
    category:Literal['waterlogging','road','drainage','water','air_quality','traffic','infrastructure','other']
    location:str=Field(min_length=3,max_length=200)
    description:str=Field(min_length=8,max_length=2000)
class ComplaintReview(BaseModel):
    status:Literal['under_review','in_progress','closed']
    note:str=Field(min_length=3,max_length=2000)
class Routing(BaseModel):
    locality:Literal['north','north_west','south','south_west','south_east','north_east','east','west','central']
    note:str=Field(min_length=3,max_length=2000)
@router.get('/feedback')
def feedback(): return {'reviews':repo.all_records('review'),'verifications':repo.all_records('verification')}
@router.post('/feedback/{identifier}/review')
def review_scenario(identifier:str,body:Review,actor:str=Depends(admin)): return review(identifier,body.decision,body.note,actor)
@router.post('/feedback/{identifier}/verification')
def verify(identifier:str,body:Verification,actor:str=Depends(admin)): return verification(identifier,body,actor)
@router.get('/complaints')
def complaints(authority_id:str|None=None):
    records=repo.all_records('complaint')
    return [r for r in records if r.get('authority_id')==authority_id] if authority_id else records
@router.get('/authorities')
def authority_queues(city_id:str='delhi'):
    from backend.services.authority_service import authorities
    return authorities(city_id)
@router.post('/complaints',status_code=201)
def complain(body:Complaint):
    from backend.services.city_service import city
    from backend.services.authority_service import assign
    city(body.city_id)
    return repo.append('complaint',{**body.model_dump(),**assign(body.city_id,body.locality),'status':'submitted','history':[],
        'provenance':'Civilian report assigned to a CivicFlux locality queue; external government delivery not connected'})
@router.post('/complaints/{identifier}')
def update(identifier:str,body:ComplaintReview,actor:str=Depends(admin)): return repo.update_complaint(identifier,body.status,body.note,actor)
@router.post('/complaints/{identifier}/route')
def route_complaint(identifier:str,body:Routing,actor:str=Depends(admin)):
    return repo.route_complaint(identifier,body.locality,body.note,actor)
@router.get('/audit')
def audit(actor:str=Depends(admin)): return repo.audit()
