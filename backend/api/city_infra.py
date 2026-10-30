"""Shared, read-only city context. Operational PIN permissions are unchanged."""
import json
from fastapi import APIRouter,Depends
from backend.auth import admin
from backend.scope import current
from backend.data_integration.service import manifest,PROCESSED
from backend.services.civic_service import SOURCES
from project_paths import DATA
router=APIRouter(prefix='/api/admin',tags=['City infrastructure reference'])
@router.get('/city-infra')
def city_infra(actor:str=Depends(admin)):
    cid=current()['city_id'];m=manifest()
    result={'city_id':cid,'city_name':{'delhi':'Delhi','chennai':'Chennai','chandigarh':'Chandigarh'}[cid],
      'scope':'City-wide reference, identical for every postal area in this city. Not a deployable inventory or operational budget.',
      'reference':None,'sources':SOURCES[cid],'layers':[],'reservoirs':None}
    if cid=='delhi':result['reference']=json.loads((DATA/'reference/delhi_reference.json').read_text())
    else:
        result['layers']=[{k:s.get(k) for k in ('id','title','status','records_out','source_last_updated','attribution','licence','url','error')} for s in m['sources'] if s['city']==cid]
        p=PROCESSED/'derived/reservoirs.json'
        if cid=='chennai' and p.exists():
            data=json.loads(p.read_text());result['reservoirs']=[{'name':r['name'],'last_month':r['last_month'],'latest_mcft':next((v['mcft'] for v in reversed(r['series']) if v['mcft'] is not None),None)} for r in data['reservoirs']]
    return result
