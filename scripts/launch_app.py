"""Launch only this checkout, after validating its frontend and chosen port."""
from pathlib import Path
import argparse
import os
import re
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=int(os.getenv('CIVICFLUX_PORT', '8001')))
args = parser.parse_args()
if not 1 <= args.port <= 65535:
    parser.error('Port must be between 1 and 65535.')
index = ROOT / 'frontend/dist/index.html'
if not index.is_file():
    raise SystemExit('Frontend build missing. Run the platform setup or START-CIVICFLUX launcher first.')
assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', index.read_text(encoding='utf-8'))
if not assets or any(not (ROOT / 'frontend/dist' / asset.lstrip('/')).is_file() for asset in assets):
    raise SystemExit('Frontend build is incomplete. Rerun the platform setup to rebuild it.')
with socket.socket() as probe:
    # A recently stopped POSIX server can leave TIME_WAIT sockets; match uvicorn's
    # address reuse without enabling SO_REUSEPORT or weakening Windows exclusivity.
    if os.name != 'nt':
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind(('127.0.0.1', args.port))
    except OSError:
        raise SystemExit(f'Port {args.port} is already in use. Close the OLD CivicFlux terminal with Ctrl+C, then start again. Do not open the old server address.')
# A shell setting left over from another clone must not select that clone's files.
os.environ['CIVICFLUX_ROOT'] = str(ROOT)
os.environ['PYTHONUTF8'] = '1'
sys.path.insert(0, str(ROOT))
import uvicorn
from backend.main import app
print(f'CivicFlux website: http://127.0.0.1:{args.port}/ | Administrator login: use your configured account', flush=True)
uvicorn.run(app, host='127.0.0.1', port=args.port)
