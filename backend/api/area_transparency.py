"""Area-scoped public finance summaries and authenticated expenditure entries."""
import json,math
from uuid import uuid4
from datetime import date
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field,ConfigDict
from backend.auth import admin
from backend.db.connection import connection
from backend.services.civic_service import verify_pin
from backend.services.administration import require_record
from backend.db import repository
router=APIRouter(prefix='/api/civic',tags=['Area transparency'])
def initialize():
 with connection() as db:db.execute('CREATE TABLE IF NOT EXISTS area_expenditures(id TEXT PRIMARY KEY,budget_id TEXT NOT NULL,amount INTEGER NOT NULL,paid_on TEXT NOT NULL,reference TEXT NOT NULL,actor TEXT NOT NULL,created TEXT NOT NULL)')
class Location(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 latitude:float=Field(ge=-90,le=90)
 longitude:float=Field(ge=-180,le=180)
 accuracy:float=Field(ge=0)
@router.post('/location')
def locate(body:Location):
 if body.accuracy>1500:return {'status':'manual_required','reason':'Location accuracy is too broad. Select your postal area manually.'}
 with connection() as db:rows=db.execute('SELECT a.city_id,a.pincode,a.area_name,a.latitude,a.longitude FROM admins a JOIN pincodes p ON a.pincode=p.pincode WHERE p.is_active=1 AND a.latitude IS NOT NULL AND a.longitude IS NOT NULL').fetchall()
 def distance(p):
  a,b=map(math.radians,[body.latitude,p['latitude']]);dx=b-a;dy=math.radians(p['longitude']-body.longitude)
  return 12742*math.asin(min(1,math.sqrt(math.sin(dx/2)**2+math.cos(a)*math.cos(b)*math.sin(dy/2)**2)))
 nearest=min(rows,key=distance) if rows else None
 if not nearest or distance(nearest)>5:return {'status':'manual_required','reason':'No supported postal reference is close enough. Select a listed city and PIN.'}
 return {'status':'approximate','city_id':nearest['city_id'],'pincode':nearest['pincode'],'area':nearest['area_name'],'note':'Nearest registered postal reference, not a verified boundary. Check or correct your PIN.'}
@router.get('/monetary/{city_id}')
def history(city_id:str,pincode:str=Query(pattern=r'^[0-9]{6}$'),fiscal_year:str|None=None):
 verify_pin(city_id,pincode)
 with connection() as db:
  budgets=[dict(b) for b in db.execute('SELECT id,budget,fiscal_year FROM locality_budgets WHERE city_id=? AND pincode=? AND is_active=1',(city_id,pincode))]
  years=sorted({b['fiscal_year'] for b in budgets},reverse=True);year=fiscal_year or (years[0] if years else None);selected=[b for b in budgets if b['fiscal_year']==year];ids={b['id'] for b in selected}
  expenses=[dict(e) for e in db.execute('SELECT budget_id,amount,paid_on FROM area_expenditures') if e['budget_id'] in ids]
  plans={row['id']:json.loads(row['body']) for row in db.execute("SELECT id,body FROM records WHERE kind='locality_plan'")}
  reserved=sum(json.loads(row['body'])['requirements']['budget'] for row in db.execute("SELECT body FROM resource_reservations WHERE status='reserved'") if plans.get(json.loads(row['body']).get('scenario_id'),{}).get('budget_id') in ids)
 return {'city_id':city_id,'pincode':pincode,'fiscal_year':year,'fiscal_years':years,'budgets':selected,'allocated':sum(b['budget'] for b in selected) if selected else None,'spent':sum(e['amount'] for e in expenses) if expenses else None,'reserved':reserved,'expense_count':len(expenses),'note':'Recorded allocation and expenditure for this PIN and fiscal year only. Reservations are plans, not paid expenditure. Missing records do not establish zero spending.'}
class Expense(BaseModel):
 model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
 budget_id:str
 amount:int=Field(gt=0,le=1000000000)
 paid_on:date
 reference:str=Field(min_length=3,max_length=500)
@router.post('/monetary/expenditures',status_code=201)
def record(body:Expense,actor:str=Depends(admin)):
 if body.paid_on>date.today():raise HTTPException(422,'Payment date cannot be in the future')
 with connection() as db:
  db.execute('BEGIN IMMEDIATE');b=db.execute('SELECT * FROM locality_budgets WHERE id=? AND is_active=1',(body.budget_id,)).fetchone()
  if not b:raise HTTPException(404,'Allocation not found')
  require_record(actor,dict(b))
  prior=db.execute('SELECT id FROM area_expenditures WHERE budget_id=? AND amount=? AND paid_on=? AND reference=?',(body.budget_id,body.amount,body.paid_on.isoformat(),body.reference)).fetchone()
  if prior:return {'id':prior['id'],'status':'recorded'}
  total=db.execute('SELECT COALESCE(SUM(amount),0) FROM area_expenditures WHERE budget_id=?',(body.budget_id,)).fetchone()[0]
  if total+body.amount>b['budget']:raise HTTPException(409,'Recorded expenditure would exceed this allocation')
  identifier=str(uuid4());stamp=repository.now()
  db.execute('INSERT INTO area_expenditures VALUES (?,?,?,?,?,?,?)',(identifier,body.budget_id,body.amount,body.paid_on.isoformat(),body.reference,actor,stamp))
  db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(stamp,actor,'area_expenditure_recorded',identifier,json.dumps({'budget_id':body.budget_id,'amount':body.amount})))
 return {'id':identifier,'status':'recorded'}
