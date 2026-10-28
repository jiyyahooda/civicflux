"""Explicit locality funding, reusable OR-Tools plans and existing atomic approval."""
import json
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field,ConfigDict
from backend.auth import admin
from backend.db.connection import connection
from backend.db import repository as repo
from backend.services.administration import require_scope,require_record,require_city,visible
from backend.services.civic_service import verify_pin
from backend.api.resources import describe,current,Decision,decide
from backend.optimizer import plan_localities
router=APIRouter(prefix='/api/locality-planning',tags=['locality plans'])

class Budget(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    city_id:str
    pincode:str
    pool_id:str
    budget:int=Field(ge=0,le=1000000000)
    severity_weight:float=Field(default=.6,ge=0,le=1)
    population_weight:float=Field(default=.4,ge=0,le=1)
    fiscal_year:str=Field(min_length=4,max_length=20)
    source_ref:str=Field(min_length=3,max_length=500)

@router.post('/budgets',status_code=201)
def create_budget(body:Budget,actor:str=Depends(admin)):
    require_scope(actor,body.city_id,body.pincode);verify_pin(body.city_id,body.pincode)
    if body.severity_weight+body.population_weight<=0:raise HTTPException(422,'At least one priority weight must be positive')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT body FROM resource_pools WHERE id=?',(body.pool_id,)).fetchone()
        if not row:raise HTTPException(404,'Resource inventory not found')
        pool=json.loads(row['body']);require_record(actor,pool)
        if pool['city_id']!=body.city_id or (pool.get('pincode') and pool['pincode']!=body.pincode):raise HTTPException(422,'Inventory jurisdiction does not match the locality')
        if not current(pool):raise HTTPException(409,'Inventory shift has expired')
        assigned=db.execute('SELECT COALESCE(SUM(budget),0) total FROM locality_budgets WHERE pool_id=? AND is_active=1',(body.pool_id,)).fetchone()['total']
        if assigned+body.budget>pool['budget']:raise HTTPException(409,'Locality funding declarations exceed this inventory budget')
        identifier=str(uuid4());stamp=repo.now()
        db.execute('INSERT INTO locality_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,1)',(identifier,body.city_id,body.pincode,body.pool_id,body.budget,body.severity_weight,body.population_weight,body.fiscal_year,body.source_ref,actor,stamp))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(stamp,actor,'locality_budget_declared',identifier,json.dumps({'pincode':body.pincode,'budget':body.budget})))
        return dict(db.execute('SELECT * FROM locality_budgets WHERE id=?',(identifier,)).fetchone())

@router.get('/budgets')
def budgets(city_id:str,actor:str=Depends(admin)):
    require_city(actor,city_id)
    with connection() as db:rows=[dict(r) for r in db.execute('SELECT * FROM locality_budgets WHERE city_id=? AND is_active=1',(city_id,))]
    return [r for r in rows if visible(actor,r)]

class Assessment(BaseModel):
    model_config=ConfigDict(extra='forbid')
    budget_id:str
    name:str=Field(default='Locality response proposal',min_length=3,max_length=100)
    duration_hours:float=Field(default=8,gt=0,le=24,allow_inf_nan=False)

@router.post('/plans',status_code=201)
def assess(body:Assessment,actor:str=Depends(admin)):
    with connection() as db:
        b=db.execute('SELECT * FROM locality_budgets WHERE id=? AND is_active=1',(body.budget_id,)).fetchone()
        if not b:raise HTTPException(404,'Locality funding declaration not found')
        b=dict(b);require_record(actor,b)
        row=db.execute('SELECT body FROM resource_pools WHERE id=?',(b['pool_id'],)).fetchone()
        if not row:raise HTTPException(404,'Resource inventory not found')
        pool=describe(db,json.loads(row['body']));require_record(actor,pool)
        if not pool['current']:raise HTTPException(409,'Inventory shift has expired')
        # Reserve only from officer-reviewed, costed packages. Unknown population stays unknown.
        active_ids=set()
        for rr in db.execute("SELECT body FROM resource_reservations WHERE status='reserved'"):
            try:reserved=json.loads(rr['body']);repo.get('locality_plan',reserved['scenario_id']);active_ids.update(reserved.get('assignments',{}))
            except HTTPException:pass
        prior_spend=0
        for rr in db.execute("SELECT body FROM resource_reservations WHERE status='reserved'"):
            res=json.loads(rr['body'])
            record=db.execute("SELECT body FROM records WHERE id=? AND kind='locality_plan'",(res['scenario_id'],)).fetchone()
            if record and json.loads(record['body']).get('budget_id')==body.budget_id:prior_spend+=res['requirements']['budget']
    eligible=[];omitted=[]
    for report in repo.all_records('complaint'):
        if report['city_id']!=b['city_id'] or report.get('postal_code')!=b['pincode'] or report['status']=='closed':continue
        if report.get('validation')!='valid' or not report.get('damage_priority') or not report.get('intervention_cost') or report['id'] in active_ids:
            omitted.append({'id':report['id'],'reason':'Needs officer validation, severity and costed package, or is already reserved.'});continue
        eligible.append({'case_id':report['id'],'report_updated_at':report.get('updated_at'),'node_id':report['id'],'title':report.get('title',report['category']),'pincode':b['pincode'],'damage_priority':report['damage_priority'],'severity':{'Low':1,'Medium':2,'High':3,'Critical':4}[report['damage_priority']], 'affected_people_count':report.get('affected_people_count'),'population_basis':report.get('population_basis','unknown'),'cost':report['intervention_cost'],'crew_type':report.get('crew_type','drain'),'duration_hours':report.get('duration_hours',1),'pumps_required':report.get('required_pumps',0),'required_crews':report.get('required_crews',1),'required_workers':report.get('required_workers',1),'required_vehicles':report.get('required_vehicles',0)})
    if not eligible:raise HTTPException(409,'No unreserved, validated reports have an assessed severity and costed intervention package in this PIN')
    capacity=dict(pool['available']);capacity['budget']=max(0,min(capacity['budget'],b['budget']-prior_spend))
    remaining_shift=max(0,(datetime.fromisoformat(pool['valid_until'])-datetime.now(timezone.utc)).total_seconds()/3600)
    capacity['work_window_hours']=min(body.duration_hours,remaining_shift)
    capacity['crew_hours']={k:min(v,pool['available']['crews']*min(body.duration_hours,remaining_shift)) for k,v in capacity['crew_hours'].items()}
    allocation=plan_localities(eligible,capacity,b['severity_weight'],b['population_weight'])
    return repo.append('locality_plan',{'city_id':b['city_id'],'pincode':b['pincode'],'pool_id':pool['id'],'budget_id':b['id'],'name':body.name,'incident_ids':[c['case_id'] for c in allocation['comparisons']['CP-SAT']['selected']],'allocation':allocation,'duration_hours':body.duration_hours,'omitted':omitted,'internal_review_status':'pending','external_dispatch':False,'synthetic':False,'basis':'Officer-assessed claims and explicitly declared resources; no causal outcome prediction.'},actor,'locality_plan_proposed')

@router.get('/plans')
def plans(city_id:str,actor:str=Depends(admin)):
    require_city(actor,city_id)
    from backend.api.resources import plan_status_record
    return [plan_status_record(p) for kind in ('locality_plan','scenario') for p in repo.all_records(kind) if p['city_id']==city_id and visible(actor,p)]

@router.post('/plans/{identifier}/decision')
def decision(identifier:str,body:Decision,actor:str=Depends(admin)):
    return decide(identifier,body,actor)


@router.get('/summary')
def summary(city_id:str,actor:str=Depends(admin)):
    require_city(actor,city_id)
    reports=[r for r in repo.all_records('complaint') if r['city_id']==city_id and visible(actor,r)]
    declared=budgets(city_id,actor)
    pins=sorted({r.get('postal_code') for r in reports if r.get('postal_code')}|{b['pincode'] for b in declared})
    result=[]
    for pin in pins:
        items=[r for r in reports if r.get('postal_code')==pin and r['status']!='closed']
        assessed=[r for r in items if r.get('validation')=='valid']
        people=[r['affected_people_count'] for r in assessed if r.get('affected_people_count') is not None]
        result.append({'pincode':pin,'reported_problems':len(items),'verified_reports':len(assessed),'severity_distribution':{level:sum(r.get('damage_priority')==level for r in assessed) for level in ['Low','Medium','High','Critical']},'assessed_population_estimates_sum':sum(people) if people else None,'unknown_population_reports':sum(r.get('affected_people_count') is None for r in assessed),'declared_locality_budget':sum(b['budget'] for b in declared if b['pincode']==pin),'population_note':'Sum of officer-recorded estimates; reports may overlap. This is not a count of unique exposed residents.'})
    return {'rows':result,'unassigned_legacy_reports':sum(not r.get('postal_code') for r in reports)}
