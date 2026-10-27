"""Package every project file, retaining link metadata without junction loops."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import posixpath
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT.parent/'CivicFlux-Complete.zip'
if OUTPUT.is_relative_to(ROOT) or OUTPUT.exists():
    raise SystemExit('Choose a new output ZIP outside the project folder.')
TEMP_OUTPUT=OUTPUT.with_name(OUTPUT.name+'.partial')

files=[]
directories=[]
links=[]
for folder, names, filenames in os.walk(ROOT, followlinks=False):
    base=Path(folder)
    directories.append(base.relative_to(ROOT).as_posix())
    regular=[]
    for name in sorted(names):
        path=base/name
        if path.is_symlink() or path.is_junction():
            target=path.resolve(strict=True)
            links.append({'path':path.relative_to(ROOT).as_posix(),
                          'target':target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else str(target),
                          'internal':target.is_relative_to(ROOT),'directory':True})
        else:
            regular.append(name)
    names[:]=regular
    for name in sorted(filenames):
        path=base/name
        if path.is_symlink():
            target=path.resolve(strict=False)
            links.append({'path':path.relative_to(ROOT).as_posix(),
                          'target':target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else os.readlink(path),
                          'internal':target.is_relative_to(ROOT),'directory':False})
        else:
            files.append(path)

restore=r'''# Recreate packaged Node dependency junctions after Windows ZIP extraction.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($PSScriptRoot)
$prefix = $root.TrimEnd('\') + '\'
$links = Get-Content -LiteralPath (Join-Path $root 'PACKAGED-LINKS.json') -Raw | ConvertFrom-Json
foreach ($link in $links) {
    if (-not $link.internal -or -not $link.directory) { continue }
    $path = [IO.Path]::GetFullPath((Join-Path $root $link.path))
    $target = [IO.Path]::GetFullPath((Join-Path $root $link.target))
    if (-not $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not $target.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'A packaged link leaves the project folder.'
    }
    if (Test-Path -LiteralPath $path) {
        $existing = Get-Item -LiteralPath $path -Force
        if ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
        throw "Cannot restore a link over an existing file or folder: $path. Use a fresh extraction or run pnpm install in frontend."
    }
    if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw "Missing packaged dependency: $target" }
    New-Item -ItemType Junction -Path $path -Target $target | Out-Null
}
Write-Host 'Packaged dependency links restored. Virtual environments may still need recreation on another computer.'
'''
readme='''# CivicFlux complete archive

This archive contains every regular file in the project folder at packaging time:
all research/model versions, notebooks, datasets, source, frontend build, dependency
files, both virtual environments, reports, caches, and local SQLite/test data.
No project directories, files, credentials or session records were excluded.
The supplied reference images and PDF are included in reference_inputs/. The enclosing workspace Git repository and
the original input ZIP are outside the project root and are not duplicated here.

Windows node_modules junctions are represented by PACKAGED-LINKS.json, retaining
their targets without recursively duplicating packages or following cycles. All
internal link targets are included. After extraction, run:

  powershell -File .\\RESTORE-PACKAGED-LINKS.ps1

Alternatively, run pnpm install inside frontend to recreate the dependency links.
Virtual environments contain machine-specific interpreter paths. On another PC,
create a fresh environment using setup-windows.ps1 and a compatible Python; do not
activate the old macOS .venv. See APPLICATION.md for usage and the migration report
for model compatibility limitations. Admin demo credentials: admin / 001.

Start with START-CIVICFLUX.cmd after environment setup. The compiled frontend is
included. All nine model components have passed their supported Windows research
checks, including recovered flood and traffic models. No retraining was performed.
IMD weather and separate CAMS estimates are connected; CPCB requires your own key.

PACKAGE-MANIFEST.json records every regular file's byte length and SHA-256 hash.
The entire archive was read back and checked against this manifest.
'''
manifest=[]
total=sum(p.stat().st_size for p in files)
print(json.dumps({'stage':'packing','files':len(files),'links':len(links),'uncompressed_bytes':total}),flush=True)
with zipfile.ZipFile(TEMP_OUTPUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
    for directory in directories:
        archive.writestr('CivicFlux/'+(directory+'/' if directory!='.' else ''),b'')
    for index,path in enumerate(files,1):
        relative=path.relative_to(ROOT).as_posix()
        digest=hashlib.sha256()
        length=0
        before=path.stat()
        with path.open('rb') as source, archive.open('CivicFlux/'+relative,'w',force_zip64=True) as target:
            while block:=source.read(1024*1024):
                digest.update(block)
                target.write(block)
                length+=len(block)
        after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise RuntimeError(f'File changed during packaging: {relative}')
        manifest.append({'path':relative,'bytes':length,'sha256':digest.hexdigest()})
        if index%5000==0: print(json.dumps({'stage':'packing','completed':index,'total':len(files)}),flush=True)
    for link in links:
        destination='CivicFlux/'+link['path']
        target=posixpath.relpath(link['target'],posixpath.dirname(link['path'])) if link['internal'] else link['target']
        entry=zipfile.ZipInfo(destination)
        entry.create_system=3
        entry.external_attr=(stat.S_IFLNK | 0o777)<<16
        archive.writestr(entry,target)
    references=sorted((ROOT/'reference_inputs').glob('*'))
    for reference in references:
        if reference.is_file():
            content=reference.read_bytes()
            relative='reference_inputs/'+reference.name
            archive.writestr('CivicFlux/'+relative,content)
            manifest.append({'path':relative,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
    archive.writestr('CivicFlux/PACKAGED-LINKS.json',json.dumps(links,indent=2))
    archive.writestr('CivicFlux/RESTORE-PACKAGED-LINKS.ps1',restore)
    archive.writestr('CivicFlux/README-COMPLETE-ZIP.md',readme)
    archive.writestr('CivicFlux/PACKAGE-MANIFEST.json',json.dumps({'files':manifest,'directory_links':len(links),'source_root':str(ROOT)},indent=2))

print(json.dumps({'stage':'verifying','files':len(manifest)}),flush=True)
with zipfile.ZipFile(TEMP_OUTPUT) as archive:
    for index,entry in enumerate(manifest,1):
        digest=hashlib.sha256()
        length=0
        with archive.open('CivicFlux/'+entry['path']) as source:
            while block:=source.read(1024*1024):
                digest.update(block)
                length+=len(block)
        if digest.hexdigest()!=entry['sha256'] or length!=entry['bytes']:
            raise RuntimeError('Archive verification failed: '+entry['path'])
        if index%10000==0: print(json.dumps({'stage':'verifying','completed':index,'total':len(manifest)}),flush=True)
    for name in ['PACKAGED-LINKS.json','RESTORE-PACKAGED-LINKS.ps1','README-COMPLETE-ZIP.md','PACKAGE-MANIFEST.json']:
        archive.read('CivicFlux/'+name)
os.replace(TEMP_OUTPUT,OUTPUT)
result={'archive':str(OUTPUT),'bytes':OUTPUT.stat().st_size,'project_files':len(manifest),'links':len(links),'verified':True}
OUTPUT.with_suffix('.verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True)
