param([Parameter(Mandatory=$true)][ValidateSet('backend','frontend')][string]$Service)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location (Join-Path $PSScriptRoot '..')
if ($Service -eq 'backend') {
    $python = Join-Path $PWD '.venv/Scripts/python.exe'
    if (-not (Test-Path $python)) { throw 'Run scripts/setup_windows.ps1 first.' }
    & $python scripts/check_runtime.py --configured
    if ($LASTEXITCODE -ne 0) { throw 'Backend configuration check failed.' }
    & $python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
} else {
    if (-not (Test-Path 'frontend/node_modules')) { throw 'Run setup first.' }
    Set-Location frontend
    corepack pnpm dev
}
if ($LASTEXITCODE -ne 0) { throw "Service exited with code $LASTEXITCODE" }
