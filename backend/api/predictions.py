from fastapi import APIRouter, HTTPException
from backend.services.prediction_service import predict,historical
from src.civicflux.serving import SCOPES
router=APIRouter(prefix='/api/predictions',tags=['research inference'])
def check(component):
    if component not in SCOPES: raise HTTPException(404,'Unknown component')
@router.get('/outlook/{city_id}')
async def current_outlook(city_id:str):
    from backend.services.outlook_service import outlook
    return await outlook(city_id)
@router.get('/{component}/series')
def series(component:str):
    check(component)
    if component not in {'rainfall','aqi','traffic'}: raise HTTPException(422,'No supported forecast series for this component')
    import pandas as pd
    from project_paths import PROJECT_ROOT
    from src.civicflux.serving import json_safe,directory_for
    frame=pd.read_csv(directory_for(PROJECT_ROOT,component)/'test_predictions.csv').head(72)
    return {'kind':'saved holdout research results','component':component,'rows':json_safe(frame.to_dict('records'))}
@router.get('/{component}/example')
def example(component:str):
    check(component)
    try: return historical(component)
    except FileNotFoundError: raise HTTPException(503,'Historical dataset unavailable. Follow DATASET_GUIDE.md to install the original data.')
@router.get('/{component}/fixture')
def input_fixture(component:str):
    check(component)
    from src.civicflux.integration import fixture
    from project_paths import PROJECT_ROOT
    try: return fixture(component,PROJECT_ROOT)
    except FileNotFoundError: raise HTTPException(503,'Historical dataset unavailable. Follow DATASET_GUIDE.md to install the original data.')
@router.post('/{component}')
def inference(component:str,body:dict):
    check(component);return predict(component,body)
