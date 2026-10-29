"""Offline integrity gate plus bounded, optional cache warming for non-Delhi PINs."""
import argparse,asyncio,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.data_pipeline import verify,read_manifest
from backend.db.repository import initialize
from backend.data_integration.service import pins,conditions
async def warm():
    initialize()
    semaphore=asyncio.Semaphore(4)
    async def one(pin):
        async with semaphore:
            value=await conditions(pin)
            print(('WARN' if value['stale'] else 'PASS')+' live cache '+pin+' air='+str(value['air'] is not None)+' river='+str(value['river'] is not None),flush=True)
    await asyncio.gather(*(one(pin) for pin in pins()))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--warm',action='store_true');args=p.parse_args()
    good=verify(strict=True)
    print('PASS parsed manifest with '+str(len(read_manifest()['sources']))+' sources')
    print('Delhi excluded from cache warming and data updates.')
    if args.warm:asyncio.run(warm())
    sys.exit(0 if good else 1)
