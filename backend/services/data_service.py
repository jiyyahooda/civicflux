"""Validate provenance, identity, units and source-time freshness."""
import math
from datetime import datetime,timezone


def normalize(payload,city,source):
    if payload['source']!=source or payload['city_id']!=city['id']:raise ValueError('Source/city identity mismatch')
    estimate=source=='CAMS'
    if not estimate:
        mapped=city.get('station_mapping') or {}
        if source=='IMD' and payload['station_id'] not in mapped.get(source,[]):raise ValueError('Unmapped station')
        if source=='CPCB' and payload.get('station_id') not in mapped.get('CPCB',[]) and payload.get('station_mapping_method')!='provider city/state identity and coordinates':raise ValueError('Unverified CPCB station identity')
    stamp=datetime.fromisoformat(payload['observed_at'].replace('Z','+00:00'))
    if stamp.tzinfo is None:raise ValueError('Timezone-aware source timestamp required')
    age=(datetime.now(timezone.utc)-stamp).total_seconds()
    if age<0:raise ValueError('Future observation/estimate valid time')
    allowed={'IMD':{'rainfall':'mm','temperature':'degC','humidity':'%','pressure':'hPa'},
             'CPCB':{'pm25':'ug/m3','aqi':'index'},'CAMS':{'pm25':'ug/m3','pm10':'ug/m3','us_aqi':'US AQI'}}[source]
    for metric,reading in payload['readings'].items():
        if source=='CPCB':
            valid=(metric.startswith('reported_') and reading['unit']=='publisher value; unit unverified') or (metric in allowed and reading['unit']==allowed[metric])
        else:valid=metric in allowed and reading['unit']==allowed[metric]
        value=reading['value']
        if not valid or isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):raise ValueError('Unsupported measurement or unit')
        if metric!='temperature' and value<0:raise ValueError('Negative reading')
        if metric=='humidity' and value>100:raise ValueError('Invalid relative humidity')
    if not payload['readings']:raise ValueError('Empty source values')
    limit=min(payload.get('freshness_limit_seconds',10800),{'IMD':21600,'CPCB':10800,'CAMS':10800}[source])
    fresh=age<=limit and not payload.get('fetch_warning')
    return {**payload,'status':'fresh' if fresh else 'stale','age_seconds':round(age),
        'kind':'model_estimate' if estimate else 'observation','model_input_eligible':False,
        'evidence_type':'model_estimate' if estimate else 'station_observation'}
