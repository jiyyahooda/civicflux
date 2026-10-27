"""Exercise the real platform launcher and built site with disposable runtime data."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'frontend/dist/index.html').exists():
    raise SystemExit('Run the platform setup script first; the frontend build is required.')
command = (['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            str(ROOT / 'scripts/start_windows.ps1')] if os.name == 'nt'
           else ['bash', str(ROOT / 'scripts/start_mac.sh')])
with tempfile.TemporaryDirectory(prefix='civicflux-launch-') as temp:
    env = os.environ.copy()
    env.update(CIVICFLUX_DB=str(Path(temp) / 'test.sqlite3'),
               CIVICFLUX_PUBLIC_FEEDS='0', CIVICFLUX_ADMIN_ID='admin',
               CIVICFLUX_ADMIN_PASSWORD='001', CIVICFLUX_ROOT=str(ROOT))
    with (Path(temp) / 'server.log').open('w+', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            with httpx.Client(base_url='http://127.0.0.1:8001', timeout=5) as client:
                for attempt in range(60):
                    if process.poll() is not None:
                        log.seek(0)
                        raise AssertionError('Launcher stopped early: ' + log.read()[-2000:])
                    try:
                        if client.get('/api/health').status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(.5)
                else:
                    raise AssertionError('Launcher did not become healthy within 30 seconds.')
                page = client.get('/')
                assert page.status_code == 200 and 'id="root"' in page.text
                assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', page.text)
                assert assets, 'Compiled frontend asset references missing'
                for asset in assets:
                    response = client.get(asset)
                    assert response.status_code == 200 and not response.headers.get('content-type','').startswith('text/html'), asset
                assert client.post('/api/auth/login', json={'username':'admin','password':'001'}).status_code == 200
                geo = client.get('/api/maps/geography/delhi').json()
                assert len(geo['assets']) == 40
                assert client.get('/api/reference/delhi').status_code == 200
                assert len(client.get('/api/models').json()) == 9
                print('PASS: real launcher, built HTML/JS/CSS, admin login, 40 map assets, references and nine model components.')
        finally:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            else:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
