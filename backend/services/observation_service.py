from datetime import datetime,timezone
import asyncio
from backend.integrations import imd,cpcb,air_quality
from .city_service import city
from .data_service import normalize


async def observations(identifier,reference=None,pincode=None):
    configuration=dict(city(identifier))
    if reference is not None:configuration.update(map_reference=reference,pincode=pincode)
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
    from backend.scope import current
    if current() or pincode:
        results=[await load('CAMS',air_quality)] if configuration['map_reference'] else []
        return {'city_id':identifier,'pincode':pincode or current()['pincode'],'checked_at':datetime.now(timezone.utc).isoformat(),'feeds':results,'map_reference':configuration['map_reference'],'notice':'Provider grid at approximate GeoNames postal reference. Not a measured postal boundary.'}
    results=await asyncio.gather(load('IMD',imd),load('CPCB',cpcb),load('CAMS',air_quality))
    return {'city_id':identifier,'checked_at':datetime.now(timezone.utc).isoformat(),'feeds':results,
        'map_reference':configuration['map_reference'],
        'notice':'Measured IMD weather, official CPCB access, and CAMS model estimates are distinct sources. None automatically feed the research models or dispatch interventions.'}
