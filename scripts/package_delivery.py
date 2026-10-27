"""Build and verify the complete portable CivicFlux delivery archive."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import zipfile
from contextlib import closing

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=Path(sys.argv[1]).resolve()
if OUTPUT.is_relative_to(ROOT) or OUTPUT.exists():
    raise SystemExit('Choose a new output ZIP outside the project directory.')
OMIT={'.venv','.venv-windows','node_modules','.cache','.jupyter','.pytest_cache',
      '__pycache__','.ipynb_checkpoints','.git','.codex','.aws'}
files=[];directories=[];excluded=[]
for folder,names,filenames in os.walk(ROOT,followlinks=False):
    base=Path(folder);directories.append(base.relative_to(ROOT).as_posix())
    kept=[]
    for name in sorted(names):
        path=base/name
        if name in OMIT or path.is_symlink() or path.is_junction():
            excluded.append({'path':path.relative_to(ROOT).as_posix()+'/', 'reason':'Installed runtime, cache, local tooling or link'})
        else:kept.append(name)
    names[:]=kept
    for name in sorted(filenames):
        path=base/name;relative=path.relative_to(ROOT).as_posix()
        private=(name=='.env' or (name.startswith('.env.') and name!='.env.example'))
        transient=(name=='.DS_Store' or name.endswith(('.pyc','.pyo','.tsbuildinfo','-wal','-shm','-journal')) or (relative.startswith('var/') and name.endswith('.log')))
        if private or transient or path.is_symlink():
            excluded.append({'path':relative,'reason':'Private configuration' if private else 'Transient runtime file or link'})
        else:files.append((path,relative))

references=sorted((ROOT/'reference_inputs').glob('*'))
for reference in references:
    if reference.is_file():files.append((reference,'reference_inputs/'+reference.name))

readme='''# CivicFlux — complete portable delivery

Includes backend, frontend source and compiled dist, all research source modules,
notebooks, datasets, original model versions and Windows portable exports, city
configuration, tests, reports, screenshots, package locks, requirements, launchers,
the CPCB setup guide, and the supplied reference images/PDF.

Nothing was retrained, regenerated or removed from the source project to package it.
Installed Python environments, node_modules, caches, private .env files, live logs
and transient runtime files are excluded. Dependency declarations are included.
Every packaged SQLite database is a consistent backup; authentication sessions are
cleared in the packaged copy only. Saved records are preserved; source databases
are not changed. See PACKAGE-MANIFEST.json for the exact inventory and exclusions.

## Run after extracting

Open a terminal in the extracted CivicFlux folder. Install compatible Python 3.12
if needed, then create a fresh environment and install the serving dependencies:

    py -3.12 -m venv .venv-windows
    .\\.venv-windows\\Scripts\\python.exe -m pip install -r requirements-serving.txt

Run START-CIVICFLUX.cmd and open http://127.0.0.1:8000/.
Local admin credentials: admin / 001 (override in your own .env if needed).
The compiled frontend is included. To edit/rebuild it, install Node.js and pnpm,
then run pnpm install --frozen-lockfile and pnpm build in frontend/.

The current interface has a cursor-responsive Three.js globe, scroll chapters,
top navigation, city search, live weather and separate modelled-air context,
14-day weather outlook, scenario planning, locality queues and admin controls.
Existing model scope, review permissions and approval restrictions remain intact.

Create your own .env from .env.example. See CPCB_SETUP.md for personal-key setup;
no private API key is shipped. IMD/CAMS require network/provider availability.
Reference inputs are design materials, not executable instructions.

All archived file bytes and hashes have been read back and verified.
'''
manifest=[];database_snapshots=[]
partial=OUTPUT.with_name(OUTPUT.name+'.partial')
print(json.dumps({'stage':'packing','files':len(files),'source_bytes':sum(p.stat().st_size for p,_ in files)}),flush=True)
stage_parent=ROOT/'.cache'
stage_parent.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='delivery-',dir=stage_parent) as stage:
    if not Path(stage).resolve().is_relative_to(stage_parent.resolve()):raise RuntimeError('Unsafe temporary staging path')
    with zipfile.ZipFile(partial,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as archive:
        for directory in directories:archive.writestr('CivicFlux/'+('' if directory=='.' else directory+'/'),b'')
        for index,(path,relative) in enumerate(files,1):
            source=path
            with path.open('rb') as probe:is_sqlite=probe.read(16)==b'SQLite format 3\x00'
            if is_sqlite:
                source=Path(stage)/f'{index}.sqlite3'
                with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=30)) as original, closing(sqlite3.connect(source)) as snapshot:
                    original.backup(snapshot)
                    sessions=snapshot.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sessions'").fetchone()
                    if sessions:snapshot.execute('DELETE FROM sessions')
                    snapshot.commit()
                    if sessions:snapshot.execute('VACUUM')
                database_snapshots.append({'path':relative,'sessions_cleared':bool(sessions)})
            before=source.stat();digest=hashlib.sha256();length=0
            with source.open('rb') as stream,archive.open('CivicFlux/'+relative,'w',force_zip64=True) as target:
                while block:=stream.read(1024*1024):
                    digest.update(block);target.write(block);length+=len(block)
            after=source.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('File changed while packaging: '+relative)
            manifest.append({'path':relative,'bytes':length,'sha256':digest.hexdigest()})
            if index%500==0:print(json.dumps({'stage':'packing','completed':index,'total':len(files)}),flush=True)
        archive.writestr('CivicFlux/README-DELIVERY.md',readme)
        archive.writestr('CivicFlux/PACKAGE-MANIFEST.json',json.dumps({'files':manifest,'excluded':excluded,'database_snapshots':database_snapshots},indent=2))

print(json.dumps({'stage':'verifying','files':len(manifest)}),flush=True)
with zipfile.ZipFile(partial) as archive:
    names=archive.namelist()
    if len(names)!=len(set(names)):raise RuntimeError('Duplicate archive entries')
    for index,entry in enumerate(manifest,1):
        digest=hashlib.sha256();length=0
        with archive.open('CivicFlux/'+entry['path']) as stream:
            while block:=stream.read(1024*1024):digest.update(block);length+=len(block)
        if length!=entry['bytes'] or digest.hexdigest()!=entry['sha256']:raise RuntimeError('Verification failed: '+entry['path'])
        if index%1000==0:print(json.dumps({'stage':'verifying','completed':index,'total':len(manifest)}),flush=True)
    archive.read('CivicFlux/README-DELIVERY.md');archive.read('CivicFlux/PACKAGE-MANIFEST.json')
os.replace(partial,OUTPUT)
digest=hashlib.sha256()
with OUTPUT.open('rb') as stream:
    while block:=stream.read(1024*1024):digest.update(block)
result={'archive':str(OUTPUT),'bytes':OUTPUT.stat().st_size,'files':len(manifest),'sha256':digest.hexdigest(),'verified':True,'database_snapshots':len(database_snapshots),'excluded_entries':len(excluded)}
OUTPUT.with_suffix('.verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True)
