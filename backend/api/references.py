"""Read-only historical context, never deployable inventory or model input."""
from pathlib import Path
import json
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse
from project_paths import DATA
from backend.services.city_service import city
router=APIRouter(prefix='/api/reference',tags=['source-linked historical references'])

def reference(identifier):
 city(identifier)
 from backend.scope import current
 if current():return {'city_id':identifier,'pincode':current()['pincode'],'status':'unavailable','reason':'No verified infrastructure inventory has been mapped to this postal area.','operational_eligible':False}
 if identifier!='delhi':return {'city_id':identifier,'status':'unavailable','reason':'The supplied reference document covers Delhi only.','operational_eligible':False}
 return json.loads((DATA/'reference/delhi_reference.json').read_text(encoding='utf-8'))
@router.get('/delhi/source')
def source_document():
 from backend.scope import current
 if current():raise HTTPException(403,'Citywide reference is not postal-area inventory')
 return FileResponse(DATA/'reference/delhi_infrastructure_reference.pdf',media_type='application/pdf',headers={'X-Content-Type-Options':'nosniff'})
@router.get('/{identifier}')
def city_reference(identifier:str):return reference(identifier)
