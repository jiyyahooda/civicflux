"""Check a locally configured CPCB key without printing credentials or URLs."""
import argparse
import asyncio
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import config
from backend.db.repository import initialize
from backend.integrations import cpcb
from backend.services.city_service import city
from backend.services.data_service import normalize

async def check(identifier):
    import os
    if not os.getenv('DATA_GOV_IN_API_KEY','').strip():
        print('No key configured. Add DATA_GOV_IN_API_KEY to the project .env, then run again.')
        return 1
    initialize()
    try:
        configuration=city(identifier)
        payload=await cpcb.fetch(configuration)
        result=normalize(payload,configuration,'CPCB')
    except Exception:
        print('CPCB could not be verified. Check the key, provider access and network. No credentials have been printed.')
        return 1
    print('City:',identifier)
    print('Status:',result.get('status'))
    print('Station:',result.get('station_name'))
    print('Observed:',result.get('observed_at'))
    print('Stations in response:',len(payload.get('stations',[])))
    print('Complete provider page:',payload.get('pagination_complete'))
    for name,reading in (result.get('readings') or {}).items():
        print(name,':',reading['value'],reading['unit'])
    print('Publisher units remain unverified; these values are not converted to an overall AQI.')
    return 0 if result.get('status')=='fresh' else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--city',choices=['delhi','chandigarh','chennai'],default='delhi')
    sys.exit(asyncio.run(check(parser.parse_args().city)))
