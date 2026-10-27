"""Public city information, private report review, and authorized records."""
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Literal
from uuid import uuid4
import math
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator, ConfigDict
from PIL import Image, ImageOps, UnidentifiedImageError
from email_validator import validate_email, EmailNotValidError
from backend.auth import admin
from backend.db import repository as repo
from backend import config
from backend.services.city_service import city
from backend.services.civic_service import context, postal, verify_pin, SOURCES
from backend.integrations.weather import weather

router=APIRouter(prefix='/api/civic', tags=['city information and reports'])
CATEGORIES={'waterlogging','road','drainage','water','air_quality','traffic','infrastructure','other'}

def public_report(item):
    # Explicit allowlist: private email, internal notes, reviewer identity never leave this response.
    keys=('id','created','updated_at','city_id','title','category','location','description','postal_code','postal_area','status','public_reply','validation','urgency','department','coordinates','coordinates_verified','images')
    result={k:item.get(k) for k in keys}
    result['images']=[{'url':f"/api/civic/reports/{item['id']}/images/{i}",'alt':'Submitted civic issue image'} for i,_ in enumerate(item.get('images',[]))]
    result['history']=[{'status':h['status'],'time':h['time'],'note':h.get('public_reply','')} for h in item.get('public_history',[])]
    return result

@router.get('/context/{identifier}')
def city_context(identifier:str):return context(identifier)
@router.get('/weather/{identifier}')
async def current_weather(identifier:str):return await weather(identifier)
@router.get('/postal/{identifier}')
def postal_reference(identifier:str):return postal(identifier)
@router.get('/reports')
def reports(city_id:str):
    city(city_id)
    return [public_report(item) for item in repo.all_records('complaint') if item['city_id']==city_id]

@router.post('/reports',status_code=201)
async def submit_report(city_id:str=Form(...), title:str=Form(...,min_length=3,max_length=120), category:str=Form(...), location:str=Form(...,min_length=3,max_length=200), description:str=Form(...,min_length=8,max_length=2000), postal_code:str=Form(...), email:str=Form(...), latitude:float|None=Form(None), longitude:float|None=Form(None), images:list[UploadFile]=File(...)):
    configuration=city(city_id)
    if category not in CATEGORIES:raise HTTPException(422,'Choose a supported problem category')
    if not __import__('re').fullmatch('[1-9][0-9]{5}',postal_code):raise HTTPException(422,'Enter a six-digit Indian PIN')
    if not title.strip() or not location.strip() or len(description.strip())<8:raise HTTPException(422,'Enter a descriptive title, location and issue description')
    areas=verify_pin(city_id,postal_code)
    try:private_email=validate_email(email,check_deliverability=False).normalized
    except EmailNotValidError:raise HTTPException(422,'Enter a valid email address')
    if not 1<=len(images)<=3:raise HTTPException(422,'Upload one to three actual JPEG or PNG images')
    if (latitude is None)!=(longitude is None):raise HTTPException(422,'Provide both map coordinates')
    coordinates=None
    if latitude is not None:
        ref=configuration['map_reference']
        if not all(math.isfinite(x) for x in (latitude,longitude)) or abs(latitude-ref['latitude'])>0.6 or abs(longitude-ref['longitude'])>0.6:
            raise HTTPException(422,'Map pin is outside the selected city vicinity. Location still requires officer verification.')
        coordinates={'latitude':latitude,'longitude':longitude}
    sanitized=[]
    try:
        for upload in images:
            if upload.content_type not in {'image/jpeg','image/png'} and not (upload.content_type in {None,'','application/octet-stream'} and Path(upload.filename or '').suffix.lower() in {'.jpg','.jpeg','.png'}):raise HTTPException(422,'Only JPEG and PNG images are accepted; convert HEIC or other formats before uploading')
            raw=await upload.read(5*1024*1024+1)
            if len(raw)>5*1024*1024:raise HTTPException(413,'Each image must be at most 5 MB')
            try:
                with Image.open(BytesIO(raw)) as im:
                    if im.format not in {'JPEG','PNG'} or im.width*im.height>20_000_000:raise ValueError()
                    im.verify()
                with Image.open(BytesIO(raw)) as im:
                    im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((2000,2000));out=BytesIO();im.save(out,format='JPEG',quality=85)
                    sanitized.append(out.getvalue())
            except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError):raise HTTPException(422,'An uploaded file is not a valid supported image')
    finally:
        for upload in images:await upload.close()
    directory=config.DB_PATH.parent/'uploads'
    names=[]
    try:
        directory.mkdir(parents=True,exist_ok=True)
        for raw in sanitized:
            name=uuid4().hex+'.jpg';names.append(name);(directory/name).write_bytes(raw)
        item=repo.append('complaint',{'city_id':city_id,'title':title.strip(),'category':category,'location':location.strip(),'description':description.strip(),'postal_code':postal_code,'postal_area':', '.join(sorted({a['area'] for a in areas})),'email_private':private_email,'images':names,'coordinates':coordinates,'coordinates_verified':False,'status':'submitted','validation':'awaiting_review','urgency':'unassigned','department':'unassigned','public_reply':'','internal_notes':'','history':[],'public_history':[],'provenance':'Citizen report; location and claim await independent verification'})
    except Exception as exc:
        for name in names:
            try:(directory/name).unlink(missing_ok=True)
            except OSError:pass
        raise HTTPException(503,'The report could not be saved with its photos. Please try again or ask the administrator to check storage permissions.') from exc
    return public_report(item)

@router.get('/reports/{identifier}')
def report_status(identifier:str):
    return public_report(repo.get('complaint',identifier))

@router.get('/reports/{identifier}/images/{index}')
def image(identifier:str,index:int):
    item=repo.get('complaint',identifier);images=item.get('images',[])
    if index<0 or index>=len(images):raise HTTPException(404,'Image not found')
    name=images[index]
    if Path(name).name!=name:raise HTTPException(404,'Image not found')
    path=config.DB_PATH.parent/'uploads'/name
    if not path.is_file():raise HTTPException(404,'Image unavailable')
    return FileResponse(path,media_type='image/jpeg',headers={'X-Content-Type-Options':'nosniff','Cache-Control':'private, max-age=300'})

@router.get('/review')
def review_reports(city_id:str,actor:str=Depends(admin)):
    city(city_id)
    return [{**public_report(i),'email_private':i.get('email_private'),'internal_notes':i.get('internal_notes',''),'completion_evidence':i.get('completion_evidence',''),'resource_proposal':i.get('resource_proposal')} for i in repo.all_records('complaint') if i['city_id']==city_id]

class ReportReview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    category:Literal['waterlogging','road','drainage','water','air_quality','traffic','infrastructure','other']|None=None
    location:str|None=Field(default=None,min_length=3,max_length=200)
    validation:Literal['valid','invalid','needs_information','awaiting_review']
    status:Literal['submitted','under_review','in_progress','closed']
    urgency:Literal['low','normal','high','urgent','unassigned']='normal'
    department:str=Field(max_length=100)
    public_reply:str=Field(default='',max_length=2000)
    internal_notes:str=Field(default='',max_length=4000)
    completion_evidence:str=Field(default='',max_length=1000)
    coordinates_verified:bool=False
    proposed_budget:int=Field(default=0,ge=0,le=10000000)
    proposed_crew_hours:float=Field(default=0,ge=0,le=10000)
    proposed_pumps:int=Field(default=0,ge=0,le=1000)
    proposed_vehicles:int=Field(default=0,ge=0,le=1000)

@router.post('/review/{identifier}')
def review_report(identifier:str,body:ReportReview,actor:str=Depends(admin)):
    item=repo.get('complaint',identifier)
    if body.coordinates_verified and not item.get('coordinates'):raise HTTPException(422,'No reported map location is available to verify')
    if body.coordinates_verified and body.validation!='valid':raise HTTPException(422,'Verify the report before publishing its map location')
    if body.status=='closed' and not body.completion_evidence.strip():raise HTTPException(422,'Record independent completion evidence before closing')
    proposal={'budget':body.proposed_budget,'crew_hours':body.proposed_crew_hours,'pumps':body.proposed_pumps,'vehicles':body.proposed_vehicles}
    if any(proposal.values()):
        current_context=context(item['city_id'])
        pools=current_context['operational_pools']
        inventory=current_context['inventory']
        if pools:
            available={k:sum(p['available'][k] for p in pools) for k in ('budget','pumps','vehicles')}
            available['crew_hours']=sum(sum(p['available']['crew_hours'].values()) for p in pools)
        elif inventory:available=inventory[0]
        else:raise HTTPException(409,'No current authorized resource roster. Record a roster before proposing resources.')
        if any(proposal[k]>available[k] for k in proposal):raise HTTPException(422,'Resource proposal exceeds the current roster')
    data=body.model_dump(exclude_none=True);data['resource_proposal']=proposal
    data['public_history']=item.get('public_history',[])+[{'status':body.status,'public_reply':body.public_reply,'time':repo.now()}]
    return public_report(repo.revise('complaint',identifier,data,actor,'officer_report_review'))

class DatedRecord(BaseModel):
    city_id:str
    valid_from:datetime
    valid_until:datetime
    @model_validator(mode='after')
    def dates(self):
        if self.valid_from.tzinfo is None or self.valid_until.tzinfo is None or self.valid_until<=self.valid_from:raise ValueError('Provide valid timezone-aware start and end times')
        city(self.city_id);return self

class Notice(DatedRecord):
    headline:str=Field(min_length=3,max_length=200)
    area:str=Field(min_length=3,max_length=200)
    description:str=Field(min_length=8,max_length=2000)
    kind:Literal['platform_notice','official_import']='platform_notice'
    source_url:str=Field(default='',max_length=500)
    alternative_route:str=Field(default='',max_length=500)

@router.post('/notices',status_code=201)
def publish_notice(body:Notice,actor:str=Depends(admin)):
    from urllib.parse import urlsplit
    if body.kind=='official_import':
        host=urlsplit(body.source_url).hostname or ''
        allowed={'delhi':['traffic.delhipolice.gov.in','www.traffic.delhipolice.gov.in'],'chennai':['gctp.in','www.gctp.in'],'chandigarh':['portal.chandigarhpolice.gov.in','chandigarhpolice.gov.in']}[body.city_id]
        if urlsplit(body.source_url).scheme!='https' or host not in allowed:raise HTTPException(422,'Official imports require a source URL from the selected city police authority')
    elif body.alternative_route:raise HTTPException(422,'Alternative routes must come from an official imported notice')
    data=body.model_dump(mode='json');data['publisher']='CivicFlux officer' if body.kind=='platform_notice' else 'Officer-imported official source'
    return repo.append('civic_notice',data,actor,'notice_published')

class Inventory(DatedRecord):
    budget:int=Field(ge=0,le=100000000)
    crew_hours:float=Field(ge=0,le=100000)
    pumps:int=Field(ge=0,le=10000)
    vehicles:int=Field(ge=0,le=10000)
    source_ref:str=Field(min_length=3,max_length=500)
    scope:str=Field(min_length=3,max_length=200)
@router.post('/inventory',status_code=201)
def inventory(body:Inventory,actor:str=Depends(admin)):
    return repo.append('resource_inventory',body.model_dump(mode='json'),actor,'resource_roster_recorded')

class Publication(BaseModel):
    city_id:str
    category:Literal['budget','staffing','traffic_reference']
    title:str=Field(min_length=3,max_length=200)
    value:float=Field(ge=0,allow_inf_nan=False)
    unit:str=Field(min_length=1,max_length=80)
    fiscal_year:str=Field(min_length=4,max_length=20)
    source_date:datetime
    source_url:str=Field(min_length=10,max_length=500)
    scope:str=Field(min_length=3,max_length=300)
@router.post('/publications',status_code=201)
def publication(body:Publication,actor:str=Depends(admin)):
    from urllib.parse import urlsplit
    city(body.city_id)
    if urlsplit(body.source_url).scheme!='https':raise HTTPException(422,'Use an HTTPS publication source')
    return repo.append('publication',body.model_dump(mode='json'),actor,'reference_publication_recorded')

@router.get('/planning/{identifier}')
def current_planning(identifier:str,actor:str=Depends(admin)):
    current=context(identifier)
    records=[public_report(r) for r in repo.all_records('complaint') if r['city_id']==identifier and r.get('validation')=='valid' and r['status']!='closed']
    return {**current,'issues':records,'message':'No confirmed active issues in the available records.' if not records else 'Confirmed issues require an officer decision.','plans':[s for s in repo.all_records('scenario') if s['city_id']==identifier]}
