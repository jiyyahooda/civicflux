"""Readable adapters around the original serving contracts; no new prediction logic."""
from copy import deepcopy
from pathlib import Path
from io import StringIO
import csv,json,math
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
from project_paths import PROJECT_ROOT
from src.civicflux.serving import discover, serve, directory_for
from src.civicflux.integration import fixture
from backend.services.city_service import city
router=APIRouter(prefix='/api/assessments',tags=['saved prediction systems'])
LABELS={'rainfall':('Rainfall forecast','Weather and air','Delhi historical state-average rainfall; next day.'),'aqi':('PM2.5 forecast','Weather and air','Delhi historical city aggregate; next hour. Station lineage and units require validation.'),'traffic':('Traffic volume forecast','Roads and water','Anonymous historical junctions only; no mapping to named city roads.'),'flood':('Waterlogging assessment','Roads and water','Assessed hypothetical catchment; output is a calibrated scenario score, not water depth.'),'water_network':('Water network assessment','Roads and water','L-TOWN benchmark network only; weak fault-onset detection.'),'infrastructure_anomaly':('Unusual sensor readings','Infrastructure','Registered benchmark sensors only; unusual readings do not prove equipment failure.'),'cascade_risk':('Possible knock-on disruptions','Infrastructure','Declared outage on a hypothetical service network; no verified municipal mapping.'),'resource_optimization':('Resource recommendations','Planning and outcomes','Assumed candidates, costs and capacities; no real-world dispatch.'),'intervention_outcomes':('Intervention duration reference','Planning and outcomes','Duration in completed benchmark interventions; success probability is unavailable.')}
FLOOD={'rain_mm':('Rainfall','mm',0,200),'duration_h':('Storm duration','hours',1,12),'area_m2':('Catchment area','m²',10000,100000),'runoff_coefficient':('Runoff fraction','fraction',.3,.95),'drain_mm_h':('Drainage capacity','mm/hour',.2,8),'blockage':('Drain blockage','fraction',0,.9),'ponding_fraction':('Ponding area fraction','fraction',.03,.2),'initial_storage_mm':('Initial stored water','mm',0,2)}

def descriptors(component,request):
 fields=[]
 def add(key,label,unit,value,low=0,high=10000000,options=None):fields.append({'key':key,'label':label,'unit':unit,'value':value,'min':low,'max':high,'options':options})
 if component=='flood':
  for key,(label,unit,lo,hi) in FLOOD.items():add(key,label,unit,request['scenarios'][0][key],lo,hi)
 elif component=='infrastructure_anomaly':
  from src.civicflux.portable import load_bundle
  entry=next(e for e in discover(PROJECT_ROOT) if e['component']==component)
  bundle=load_bundle(PROJECT_ROOT,entry)
  add('sensor','Registered benchmark sensor','source-specific units',request.get('sensor','rainfall:Delhi'),options=list(bundle.suites))
 elif component=='cascade_risk':
  add('load','Service pressure','relative load',request['load'],.5,1.5)
  add('initial','Initial outage','asset',request['initial'][0],options=[n['id'] for n in request['graph']['nodes']])
 elif component=='resource_optimization':
  add('budget','Available budget','INR',request['resources']['budget']);add('pumps','Available pumps','count',request['resources']['pumps'],0,1000)
  for key,value in request['resources']['crew_hours'].items():add('crew_'+key,key.capitalize()+' crew time','hours',value,0,10000)
 elif component=='intervention_outcomes':
  for key,value in request['record'].items():
   if isinstance(value,(int,float)):
    low,high=(1,5) if key=='initial_severity' else (0,1) if key=='risk_score_at_assignment' else (0,10000000) if 'cost' in key else (0,100)
    add(key,key.replace('_',' ').capitalize(),'INR' if 'cost' in key else 'count' if 'count' in key else 'severity scale 1–5' if key=='initial_severity' else 'relative value',value,low,high)
   else:add(key,key.replace('_',' ').capitalize(),'category',value,options=['pump_repair','pipe_repair','drain_clear','road_barrier'] if key=='intervention_type' else ['water','road','drain'])
 return fields

@router.get('')
def catalog(city_id:str):
 city(city_id);result=[]
 for entry in discover(PROJECT_ROOT):
  c=entry['component'];title,group,note=LABELS[c];schema=json.loads((PROJECT_ROOT/entry['feature_schema']).read_text(encoding='utf-8'))
  fields=[];available=True
  try:fields=descriptors(c,fixture(c,PROJECT_ROOT))
  except FileNotFoundError:
   available=False
   if c=='infrastructure_anomaly':fields=descriptors(c,{})
  columns={}
  if c=='water_network':
   from src.civicflux.portable import load_bundle
   columns=load_bundle(PROJECT_ROOT,entry).sensors
  result.append({'measurement_columns':columns,'id':c,'title':title,'group':group,'note':note,'fields':fields,'reference_available':available,'city_prediction_available':False,'horizon':entry['horizon'],'scope':entry['geographic_scope'],'schema_field_count':len(schema),'history_columns':({'rainfall':['date','state_name','actual'],'aqi':['timestamp','location_name','pm25'],'traffic':['DateTime','Junction','Vehicles'],'infrastructure_anomaly':['time','value']}.get(c,[])),'measurement_families':(['Pressures','Flows','Levels'] if c=='water_network' else []),'supports_history_upload':c in ('rainfall','aqi','traffic','infrastructure_anomaly'),'input_help':{'infrastructure_anomaly':'CSV columns: time, value. Confirm the registered sensor units: rainfall mm, PM2.5 source concentration scale, or traffic vehicles/hour. Use the benchmark sensor identity and source timestamps.','water_network':'L-TOWN only: pressure in metres, flows in m³/hour, levels in metres. Upload matching Timestamp columns and the original registered sensor columns/order. At least 24 hours of 5-minute history is required. Naive benchmark timestamps do not establish a city timezone.'}.get(c,'Use the original entity identity, units and historical observation clock.'),'basis':'Historical benchmark' if c in ('rainfall','aqi','traffic','infrastructure_anomaly','water_network') else 'What-if assessment','notebook_count':11,'component_count':9})
 return result

class Assessment(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 city_id:str
 mode:Literal['reference','custom','city']='reference'
 values:dict[str,float|str]=Field(default_factory=dict,max_length=30)
 history_csv:str=Field(default='',max_length=200000)
 as_of:str=Field(default='',max_length=80)
 observation_time:str=Field(default='',max_length=80)
 measurement_csv:dict[str,str]=Field(default_factory=dict,max_length=3)
 units_confirmed:bool=False

def present(component,response):
 value=response['prediction'];rows=value if isinstance(value,list) else [value] if value else [];first=rows[0] if rows else {};metrics=[];series=[]
 def metric(label,v,unit=''):
  if isinstance(v,(int,float)) and math.isfinite(v):metrics.append({'label':label,'value':round(v,4),'unit':unit})
 if not response['status'].startswith('supported'):return {'status':'unavailable','summary':'Prediction not available for these conditions. Check the input scope, timestamps and required history.','metrics':[],'series':[],'intervals':[],'uncertainty_note':'No supported result was produced.'}
 if component in ('rainfall','aqi','traffic'):
  unit={'rainfall':'mm/day','aqi':'µg/m³ (benchmark convention)','traffic':'vehicles/hour'}[component]
  metric(LABELS[component][0],first.get('prediction'),unit)
  series=[{'label':str(row.get('target_time',row.get('time',''))),'value':row['prediction']} for row in rows if isinstance(row.get('prediction'),(int,float))]
  summary={'rainfall':'The saved system estimates next-day rainfall for the supplied Delhi historical sequence.','aqi':'The saved system estimates next-hour PM2.5 for the supplied Delhi historical sequence.','traffic':'The saved system estimates next-hour vehicle counts for anonymous benchmark junctions.'}[component]
 elif component=='flood':
  metric('Calibrated scenario score',first.get('simulated_flood_probability'),'0–1')
  summary='The assessed catchment '+('crosses' if first.get('scenario_alert') else 'does not cross')+' its saved scenario alert threshold. This score is not a real-city flood probability or a depth estimate.'
 elif component=='water_network':
  metric('Benchmark onset score',first.get('benchmark_onset_score'),'0–1');summary='The L-TOWN reference '+('raises' if first.get('research_alert') else 'does not raise')+' the saved alert threshold. Operational fault prediction remains unavailable.'
 elif component=='infrastructure_anomaly':
  metric('Unusual-reading score',first.get('anomaly_score'));metric('Saved alert threshold',first.get('threshold'));summary='The selected benchmark sensor '+('has an unusual reading' if first.get('alert') else 'does not cross the unusual-reading threshold')+'. This does not establish an infrastructure fault.'
 elif component=='cascade_risk':
  metric('Assets requiring review',sum(bool(row.get('review')) for row in rows),'assets');series=[{'label':row['node_id'].replace('_',' '),'value':row['risk']} for row in rows];summary='Declared outages may affect connected services in this hypothetical network. Review highlighted assets before drawing any local conclusion.'
 elif component=='resource_optimization':
  metric('Priority candidates addressed',len(first.get('selected',[])),'candidates');metric('Proposed spending',first.get('used',{}).get('budget'),'INR');metric('Pumps proposed',first.get('used',{}).get('pumps'),'pumps');summary='The existing resource planner selected feasible candidates under the supplied capacities. This is a proposal requiring human review.'
 elif component=='intervention_outcomes':
  metric('Reference resolution duration',first.get('research_resolution_hours'),'hours');summary='The saved duration model provides a benchmark estimate for the supplied intervention assumptions. It does not estimate success probability or causal benefit.'
 intervals=response.get('uncertainty',{}).get('intervals',[]) if response.get('uncertainty') else []
 return {'status':'complete','summary':summary,'metrics':metrics,'series':series,'intervals':intervals,'uncertainty_note':'90% residual prediction interval from the saved benchmark calibration; coverage is not guaranteed for a new city.' if intervals else 'A calibrated uncertainty interval is unavailable for this component. Scores are not universal confidence percentages.'}

@router.post('/{component}')
def assess(component:str,body:Assessment):
 city(body.city_id)
 if component not in LABELS:raise HTTPException(404,'Assessment not found')
 if body.mode=='city' or ((body.mode=='custom' or body.history_csv) and component in ('rainfall','aqi') and body.city_id!='delhi'):
  return {'status':'unavailable','summary':'Live local prediction is not validated for this city and input source. You can run the explicitly identified saved benchmark instead.','metrics':[],'series':[],'intervals':[],'uncertainty_note':'Uncertainty unavailable.','basis':'City applicability check','scope':LABELS[component][2]}
 if body.measurement_csv and (component!='water_network' or set(body.measurement_csv)!={'Pressures','Flows','Levels'} or any(len(v)>500000 for v in body.measurement_csv.values())):raise HTTPException(422,'Provide the three bounded, matching L-TOWN sensor CSV files')
 if (body.history_csv or body.measurement_csv) and not body.units_confirmed:raise HTTPException(422,'Confirm the displayed benchmark units before submitting history')
 try:request=deepcopy(fixture(component,PROJECT_ROOT))
 except FileNotFoundError:
  if (body.history_csv and component in ('rainfall','aqi','traffic','infrastructure_anomaly')) or (body.measurement_csv and component=='water_network'):
   from src.civicflux.serving import SCOPES,UNITS,HORIZONS
   request={'scope':SCOPES[component],'units':UNITS[component],'horizon':HORIZONS[component],'purpose':'research','mode':'simulation' if component=='water_network' else 'historical','synthetic':component=='water_network','as_of':body.as_of,'network_id':'L-TOWN'}
  else:raise HTTPException(503,'Original benchmark inputs are unavailable. Follow the dataset setup instructions.')
 allowed={f['key']:f for f in descriptors(component,request)}
 if set(body.values)-set(allowed):raise HTTPException(422,'An assessment input is outside the saved schema')
 for key,value in body.values.items():
  field=allowed[key]
  if field['options']:
   if value not in field['options']:raise HTTPException(422,'Choose a supported assessment category')
  elif not isinstance(value,(int,float)) or not math.isfinite(value) or not field['min']<=value<=field['max']:raise HTTPException(422,'Assessment value is outside the supported range')
  if component=='flood':request['scenarios'][0][key]=value
  elif component=='cascade_risk':request['initial' if key=='initial' else 'load']=[value] if key=='initial' else value
  elif component=='infrastructure_anomaly':
   if not body.history_csv:
    from src.civicflux.integration import anomaly_sensor_fixtures
    request=deepcopy(anomaly_sensor_fixtures(PROJECT_ROOT)[value])
   else:
    from src.civicflux.portable import load_bundle
    bundle=load_bundle(PROJECT_ROOT,next(e for e in discover(PROJECT_ROOT) if e['component']==component))
    request['sensor']=value;request['sensor_unit']=bundle.specs[value].unit
  elif component=='intervention_outcomes':request['record'][key]=value
  elif component=='resource_optimization':
   if key.startswith('crew_'):request['resources']['crew_hours'][key[5:]]=value
   else:request['resources'][key]=value
 if body.history_csv:
  if component not in ('rainfall','aqi','traffic','infrastructure_anomaly') or not body.as_of:raise HTTPException(422,'A forecast history and its assessment time are required')
  records=list(csv.DictReader(StringIO(body.history_csv)))
  if not records or len(records)>1000:raise HTTPException(422,'Use between 1 and 1000 history rows')
  if component=='infrastructure_anomaly':
   import pandas as pd

   try:frame=pd.read_csv(StringIO(body.history_csv))
   except Exception:raise HTTPException(422,'Invalid sensor CSV history')
   if not {'time','value'}<=set(frame):raise HTTPException(422,'Sensor history must contain time and value columns')
   sensor=request.get('sensor','rainfall:Delhi')
   from src.civicflux.portable import load_bundle
   bundle=load_bundle(PROJECT_ROOT,next(e for e in discover(PROJECT_ROOT) if e['component']==component))
   frame['sensor']=sensor;frame['invalid']=False
   request['sensor']=sensor;request['sensor_unit']=bundle.specs[sensor].unit
   records=frame.to_dict('records');request['observation_time']=body.observation_time or str(frame['time'].iloc[-1])
  request['history']=records;request['as_of']=body.as_of
 if body.measurement_csv:
  if not body.as_of or not body.observation_time:raise HTTPException(422,'Provide both observation and assessment timestamps')
  import pandas as pd
  measurements={}
  for family,text in body.measurement_csv.items():
   try:
    delimiter=';' if ';' in text.splitlines()[0] else ','
    frame=pd.read_csv(StringIO(text),sep=delimiter,decimal=',' if delimiter==';' else '.',nrows=1001)
    if len(frame)>1000 or 'Timestamp' not in frame:raise ValueError()
    for column in frame.columns:
     if column!='Timestamp':frame[column]=pd.to_numeric(frame[column],errors='raise')
    measurements[family]=frame.to_dict('records')
   except Exception:raise HTTPException(422,'Invalid sensor CSV: use Timestamp and registered numeric sensor columns')
  request['measurements']=measurements;request['as_of']=body.as_of;request['observation_time']=body.observation_time;request['network_id']='L-TOWN'
 response=serve(component,request,PROJECT_ROOT)
 result=present(component,response)
 return {**result,'basis':'User-supplied benchmark history' if body.history_csv else LABELS[component][1]+' · '+('Historical benchmark' if request['mode']=='historical' else 'What-if assessment'),'scope':LABELS[component][2],'assessment_time':request['as_of'],'city_id':body.city_id,'local_prediction':False,'input_age_hours':(response.get('freshness') or {}).get('age_hours'),'data_quality':'Serving-contract checks applied; user histories and declared units are not independently verified.'}


@router.get('/{component}/explanation')
def saved_explanation(component:str):
    """Expose saved evaluation evidence; never manufacture local SHAP attributions."""
    import hashlib
    if component not in LABELS:raise HTTPException(404,'Assessment not found')
    supported={'rainfall','aqi','traffic','flood','water_network','cascade_risk'}
    base={'component':component,'local_attribution_available':False,'note':'Global saved evaluation evidence, not causal effects or feature contributions to an individual current forecast. Local SHAP values were not exported.'}
    if component not in supported:return {**base,'status':'unavailable','features':[],'reason':'No matching feature-attribution export exists for this component. Constraint and dependency explanations remain available in Decisions.'}
    path=directory_for(PROJECT_ROOT,component)/'permutation_importance.csv'
    if not path.is_file():return {**base,'status':'unavailable','features':[],'reason':'Saved evaluation evidence is unavailable.'}
    features=[]
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.reader(stream);next(reader,None)
        for row in reader:
            if len(row)!=2:continue
            try:value=float(row[1])
            except ValueError:continue
            if math.isfinite(value):features.append({'feature':row[0],'importance':value})
    metric='Increase in held-out mean absolute error after feature shuffling' if component in {'rainfall','aqi','traffic'} else 'Drop in held-out average precision after feature shuffling'
    return {**base,'status':'available','method':'Saved permutation importance','metric':metric,'features':sorted(features,key=lambda r:r['importance'],reverse=True)[:12],'source':str(path.relative_to(PROJECT_ROOT).as_posix()),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
