$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location (Join-Path $PSScriptRoot '..')
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE). See error above." } }
foreach ($name in @('py', 'node', 'corepack')) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw "Install prerequisite: $name. See README.md." }
}
node -e 'if(parseInt(process.versions.node)<24)process.exit(1)'
Check-Exit
if (-not (Test-Path '.venv')) { py -3.13 -m venv .venv; Check-Exit }
$python = Join-Path $PWD '.venv/Scripts/python.exe'
if (-not (Test-Path $python)) { throw 'Transferred or broken .venv: rename it and rerun setup.' }
& $python -c 'import sys; assert sys.version_info[:2] == (3,13)'; Check-Exit
& $python -m pip install -r requirements-test.txt; Check-Exit
& $python -m pip check; Check-Exit
& $python scripts/check_runtime.py; Check-Exit
& $python scripts/local_config.py; Check-Exit
Push-Location frontend
try {
    corepack pnpm install --frozen-lockfile; Check-Exit
    corepack pnpm build; Check-Exit
} finally { Pop-Location }
Write-Host 'Ready. Run scripts/run_windows.ps1 backend and scripts/run_windows.ps1 frontend in separate terminals.'
