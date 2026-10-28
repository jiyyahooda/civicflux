"""Authorized operational pools and atomic internal-plan reservations.

Annual reference allocations never enter these capacities. Internal approval
reserves declared resources but does not approve research deployment or dispatch.
"""
import json
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field,ConfigDict,model_validator
from typing import Literal
from backend.auth import admin
from backend.services.administration import require_record,require_scope,require_city,visible
from backend.db.connection import connection
from backend.db import repository as repo
from backend.services.city_service import city
router=APIRouter(prefix='/api/resources',tags=['authorized resource inventory and internal review'])
SQL='''
CREATE TABLE IF NOT EXISTS resource_pools (
 id TEXT PRIMARY KEY, city_id TEXT NOT NULL, body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resource_reservations (
 id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL, pool_id TEXT NOT NULL,
 status TEXT NOT NULL, body TEXT NOT NULL,
 FOREIGN KEY(pool_id) REFERENCES resource_pools(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_live_plan_reservation ON resource_reservations(scenario_id) WHERE status='reserved';
'''

def initialize():
 with connection() as db:db.executescript(SQL)
def current(pool):
 now=datetime.now(timezone.utc)
 return datetime.fromisoformat(pool['valid_from'])<=now<=datetime.fromisoformat(pool['valid_until'])
def reservations(db,pool_id,exclude=None):
 rows=db.execute("SELECT body FROM resource_reservations WHERE pool_id=? AND status='reserved'",(pool_id,)).fetchall()
 return [json.loads(r['body']) for r in rows if json.loads(r['body'])['scenario_id']!=exclude]
def usage(items):
 total={'crews':0,'workers':0,'pumps':0,'vehicles':0,'budget':0,'crew_hours':{'water':0,'road':0,'drain':0}}
 for item in items:
  req=item['requirements']
  for key in ('crews','workers','pumps','vehicles','budget'):total[key]+=req[key]
  for key,value in req['crew_hours'].items():total['crew_hours'][key]=total['crew_hours'].get(key,0)+value
 return total
def describe(db,pool):
 used=usage(reservations(db,pool['id']))
 total={k:pool[k] for k in ('crews','workers','pumps','vehicles','budget','crew_hours')}
 free={k:total[k]-used[k] for k in ('crews','workers','pumps','vehicles','budget')}
 free['crew_hours']={k:v-used['crew_hours'].get(k,0) for k,v in pool['crew_hours'].items()}
 return {**pool,'current':current(pool),'assigned':used,'available':free}
def pools_for(identifier,public=False):
 with connection() as db:
  rows=db.execute('SELECT body FROM resource_pools WHERE city_id=?',(identifier,)).fetchall()
  results=[describe(db,json.loads(r['body'])) for r in rows]
 if public:
  keys=('id','city_id','pincode','department','service_area','specialization','valid_from','valid_until','updated_at','crews','workers','pumps','vehicles','budget','crew_hours','current','available','assigned')
  return [{k:p.get(k) for k in keys} for p in results if p['current']]
 return results

class Pool(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 city_id:str
 pincode:str|None=None
 department:str=Field(min_length=3,max_length=100)
 service_area:str=Field(min_length=3,max_length=150)
 specialization:str=Field(min_length=3,max_length=150)
 workers_on_shift:int=Field(ge=0,le=100000)
 workers:int=Field(ge=0,le=100000)
 crews:int=Field(ge=0,le=10000)
 pumps:int=Field(ge=0,le=10000)
 vehicles:int=Field(ge=0,le=10000)
 equipment:str=Field(default='',max_length=1000)
 budget:int=Field(ge=0,le=1000000000)
 crew_hours:dict[Literal['water','road','drain'],float]
 source_ref:str=Field(min_length=3,max_length=500)
 valid_from:datetime
 valid_until:datetime
 @model_validator(mode='after')
 def valid(self):
  city(self.city_id)
  if self.workers>self.workers_on_shift:raise ValueError('Available workers cannot exceed the shift roster')
  if self.crews>self.workers:raise ValueError('Available crews cannot exceed recorded available workers')
  if set(self.crew_hours)!={'water','road','drain'} or any(v<0 or v>100000 for v in self.crew_hours.values()):raise ValueError('Record water, road and drain crew-hours, including zero for unavailable specializations')
  if self.valid_from.tzinfo is None or self.valid_until.tzinfo is None or self.valid_until<=self.valid_from:raise ValueError('Valid timezone-aware shift start/end required')
  return self

def save_pool(body,actor,identifier=None):
 require_scope(actor,body.city_id,body.pincode)
 if body.pincode:
  from backend.services.civic_service import verify_pin
  verify_pin(body.city_id,body.pincode)
 pool=body.model_dump(mode='json');pool['valid_from']=body.valid_from.astimezone(timezone.utc).isoformat();pool['valid_until']=body.valid_until.astimezone(timezone.utc).isoformat();pool.update(updated_at=repo.now(),responsible_admin=actor,id=identifier or str(uuid4()))
 with connection() as db:
  db.execute('BEGIN IMMEDIATE')
  if identifier:
   old=db.execute('SELECT body FROM resource_pools WHERE id=?',(identifier,)).fetchone()
   if old is None:raise HTTPException(404,'Inventory not found')
   previous=json.loads(old['body']);require_record(actor,previous)
   if previous['city_id']!=pool['city_id'] or previous.get('pincode')!=pool.get('pincode'):raise HTTPException(422,'A resource pool cannot move to another city')
   declared=db.execute('SELECT COALESCE(SUM(budget),0) total FROM locality_budgets WHERE pool_id=? AND is_active=1',(identifier,)).fetchone()['total']
   if declared>pool['budget']:raise HTTPException(409,'Inventory budget cannot fall below active locality funding declarations')
   used=usage(reservations(db,identifier))
   if any(used[k]>pool[k] for k in ('crews','workers','pumps','vehicles','budget')) or any(used['crew_hours'][k]>pool['crew_hours'][k] for k in used['crew_hours']):raise HTTPException(409,'Inventory cannot be reduced below existing reservations; release or revise the plans first')
  # Prevent overlapping copies of the same authoritative roster from doubling capacity.
  for row in db.execute('SELECT body FROM resource_pools WHERE city_id=?',(pool['city_id'],)):
   other=json.loads(row['body'])
   if other['id']!=pool['id'] and (other['department'],other['service_area'],other['specialization'])==(pool['department'],pool['service_area'],pool['specialization']) and max(other['valid_from'],pool['valid_from'])<min(other['valid_until'],pool['valid_until']):raise HTTPException(409,'An overlapping roster already exists for this department and service area; edit it instead')
  db.execute('INSERT INTO resource_pools VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(pool['id'],pool['city_id'],json.dumps(pool)))
  db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(repo.now(),actor,'operational_inventory_updated',pool['id'],json.dumps({'city_id':pool['city_id']})))
  return describe(db,pool)

@router.get('/pools')
def list_pools(city_id:str,actor:str=Depends(admin)):
 city(city_id);require_city(actor,city_id);return [p for p in pools_for(city_id) if visible(actor,p)]
@router.post('/pools',status_code=201)
def create_pool(body:Pool,actor:str=Depends(admin)):return save_pool(body,actor)
@router.post('/pools/{identifier}')
def update_pool(identifier:str,body:Pool,actor:str=Depends(admin)):return save_pool(body,actor,identifier)

class Assignment(BaseModel):
 model_config=ConfigDict(extra='forbid')
 crews:int=Field(ge=1,le=10000)
 workers:int=Field(ge=1,le=100000)
 vehicles:int=Field(ge=0,le=10000)
 @model_validator(mode='after')
 def size(self):
  if self.workers<self.crews:raise ValueError('Assigned workers cannot be fewer than assigned crews')
  return self
class Decision(BaseModel):
 model_config=ConfigDict(extra='forbid')
 decision:Literal['approve_internal','request_changes','defer','reject','release']
 note:str=Field(min_length=3,max_length=2000)
 method:Literal['CP-SAT','utility_greedy','severity_greedy']='CP-SAT'
 pool_id:str|None=None
 assignments:dict[str,Assignment]=Field(default_factory=dict,max_length=1000)

def decide(identifier,body,actor):
 with connection() as db:
  db.execute('BEGIN IMMEDIATE')
  row=db.execute("SELECT body FROM records WHERE kind IN ('scenario','locality_plan') AND id=?",(identifier,)).fetchone()
  if row is None:raise HTTPException(404,'Plan not found')
  scenario=json.loads(row['body']);require_record(actor,scenario);reservation=None
  previous=db.execute("SELECT id,body FROM resource_reservations WHERE scenario_id=? AND status='reserved'",(identifier,)).fetchone()
  if body.decision=='approve_internal':
   poolrow=db.execute('SELECT body FROM resource_pools WHERE id=?',(body.pool_id,)).fetchone()
   if poolrow is None:raise HTTPException(409,'Choose a current authorized operational inventory')
   pool=json.loads(poolrow['body']);require_record(actor,pool)
   if pool['city_id']!=scenario['city_id'] or (pool.get('pincode') and pool.get('pincode')!=scenario.get('pincode')) or not current(pool):raise HTTPException(409,'Inventory is expired or belongs to another city')
   plan=scenario['allocation']['comparisons'][body.method];selected=plan['selected']
   if scenario.get('budget_id'):
    funding=db.execute('SELECT * FROM locality_budgets WHERE id=? AND is_active=1',(scenario['budget_id'],)).fetchone()
    if not funding or pool['id']!=funding['pool_id']:raise HTTPException(409,'The plan must use its declared locality funding and inventory')
    spent=0;requested={c['case_id'] for c in selected}
    for rr in db.execute("SELECT body FROM resource_reservations WHERE status='reserved'"):
     res=json.loads(rr['body'])
     if res['scenario_id']==identifier:continue
     record=db.execute("SELECT body FROM records WHERE kind='locality_plan' AND id=?",(res['scenario_id'],)).fetchone()
     if record:
      other=json.loads(record['body'])
      if requested.intersection(res.get('assignments',{})):raise HTTPException(409,'A selected incident already has a reserved response plan')
      if other.get('budget_id')==scenario['budget_id']:spent+=res['requirements']['budget']
    if spent+plan['used']['budget']>funding['budget']:raise HTTPException(409,'Locality funding has been reserved by another plan')
    for candidate in selected:
     report=repo.get('complaint',candidate['case_id'])
     if report.get('validation')!='valid' or report['status']=='closed' or candidate.get('report_updated_at')!=report.get('updated_at'):raise HTTPException(409,'A selected incident is no longer eligible for approval')
     package=body.assignments.get(candidate['case_id'])
     if package and (package.crews<candidate['required_crews'] or package.workers<candidate['required_workers'] or package.vehicles<candidate['required_vehicles']):raise HTTPException(422,'An assignment is below the officer-assessed package requirements')
   if not selected:raise HTTPException(409,'This plan has no candidate actions to reserve')
   if set(body.assignments)!={c['case_id'] for c in selected}:raise HTTPException(422,'Record crew, worker and vehicle packages for every selected action')
   assignments={k:v.model_dump() for k,v in body.assignments.items()}
   used=plan['used'];requirements={'crews':sum(v['crews'] for v in assignments.values()),'workers':sum(v['workers'] for v in assignments.values()),'vehicles':sum(v['vehicles'] for v in assignments.values()),'pumps':used['pumps'],'budget':used['budget'],'crew_hours':used['crew_hours']}
   reserved=usage(reservations(db,pool['id'],exclude=identifier))
   if any(requirements[k]+reserved[k]>pool[k] for k in ('crews','workers','pumps','vehicles','budget')) or any(v+reserved['crew_hours'].get(k,0)>pool['crew_hours'].get(k,0)+1e-9 for k,v in requirements['crew_hours'].items()):raise HTTPException(409,'Insufficient unreserved resources. Another plan may have reserved them; refresh the roster and revise the plan.')
   if previous:
    saved=json.loads(previous['body'])
    if saved['pool_id']==pool['id'] and saved['method']==body.method and saved['assignments']==assignments:
     decisions=[json.loads(x['body']) for x in db.execute("SELECT body FROM records WHERE kind='internal_plan_review' ORDER BY created DESC")]
     decision=next((d for d in decisions if d.get('reservation_id')==saved['id']),None)
     return {'decision':decision,'reservation':saved,'external_dispatch':False,'already_approved':True}
   if previous:db.execute("UPDATE resource_reservations SET status='released' WHERE id=?",(previous['id'],))
   reservation={'id':str(uuid4()),'scenario_id':identifier,'pool_id':pool['id'],'method':body.method,'requirements':requirements,'assignments':assignments,'created':repo.now(),'actor':actor,'scope':'Internal what-if resource reservation only','external_dispatch':False}
   db.execute('INSERT INTO resource_reservations VALUES (?,?,?,?,?)',(reservation['id'],identifier,pool['id'],'reserved',json.dumps(reservation)))
  elif previous:db.execute("UPDATE resource_reservations SET status='released' WHERE id=?",(previous['id'],))
  decision={**body.model_dump(mode='json'),'id':str(uuid4()),'scenario_id':identifier,'actor':actor,'created':repo.now(),'reservation_id':reservation['id'] if reservation else None,'external_dispatch':False,'scope':'Internal administrative decision; scientific approval rules unchanged'}
  db.execute('INSERT INTO records VALUES (?,?,?,?)',(decision['id'],'internal_plan_review',decision['created'],json.dumps(decision)))
  if scenario.get('budget_id') and body.decision=='approve_internal':scenario['incident_ids']=list(body.assignments)
  scenario['internal_review_status']=body.decision;scenario['external_dispatch']=False
  db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(scenario),identifier))
  db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(repo.now(),actor,'internal_plan_'+body.decision,identifier,json.dumps({'reservation_id':decision['reservation_id']})))
  return {'decision':decision,'reservation':reservation,'external_dispatch':False}

@router.post('/plans/{identifier}/decision')
def plan_decision(identifier:str,body:Decision,actor:str=Depends(admin)):return decide(identifier,body,actor)
@router.get('/plans/{identifier}')
def plan_status(identifier:str,actor:str=Depends(admin)):
 require_record(actor,repo.get('scenario',identifier))
 with connection() as db:
  reserved=db.execute("SELECT body FROM resource_reservations WHERE scenario_id=? AND status='reserved'",(identifier,)).fetchone()
  history=[json.loads(r['body']) for r in db.execute("SELECT body FROM records WHERE kind='internal_plan_review' ORDER BY created DESC") if json.loads(r['body'])['scenario_id']==identifier]
 return {'reservation':json.loads(reserved['body']) if reserved else None,'history':history,'external_dispatch':False}


def plan_status_record(plan):
 with connection() as db:
  row=db.execute("SELECT body FROM resource_reservations WHERE scenario_id=? AND status='reserved'",(plan['id'],)).fetchone()
  decisions=[json.loads(r['body']) for r in db.execute("SELECT body FROM records WHERE kind='internal_plan_review' ORDER BY created DESC") if json.loads(r['body']).get('scenario_id')==plan['id']]
 return {**plan,'reservation':json.loads(row['body']) if row else None,'decisions':decisions,'progress':'Internal reservation active' if row else plan.get('internal_review_status','pending')}
