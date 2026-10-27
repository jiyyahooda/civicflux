from datetime import datetime,timezone
import asyncio
from backend.integrations import imd,cpcb,air_quality
from .city_service import city
from .data_service import normalize


async def observations(identifier):
    configuration=city(identifier)
    async def load(source,adapter):
        try:
            payload=await adapter.fetch(configuration)
            if payload is None:raise ValueError('Provider returned no data')
            result=normalize(payload,configuration,source)
            if payload.get('stations'):
                result['stations']=[normalize({**station,'fetch_warning':payload.get('fetch_warning')},configuration,source) for station in payload['stations']]
            return result
        except Exception as error:
            # Integrations sanitize network failures so secrets never enter API errors.
            reason=str(error) if isinstance(error,ValueError) else 'Provider response could not be validated'
            return {'source':source,'status':'unavailable','readings':None,'reason':reason,
                'kind':'model_estimate' if source=='CAMS' else 'observation','model_input_eligible':False,
                'provider_url':cpcb.REFERENCE if source=='CPCB' else imd.REFERENCE if source=='IMD' else 'https://open-meteo.com/en/docs/air-quality-api',
                'requires_configuration':source=='CPCB'}
    results=await asyncio.gather(load('IMD',imd),load('CPCB',cpcb),load('CAMS',air_quality))
    return {'city_id':identifier,'checked_at':datetime.now(timezone.utc).isoformat(),'feeds':results,
        'map_reference':configuration['map_reference'],
        'notice':'Measured IMD weather, official CPCB access, and CAMS model estimates are distinct sources. None automatically feed the research models or dispatch interventions.'}
