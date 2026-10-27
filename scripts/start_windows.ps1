$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (-not (Test-Path '.venv/Scripts/python.exe') -or -not (Test-Path 'frontend/dist/index.html')) {
    Write-Host "First run: installing this device environment and building the website."
    & (Join-Path $PSScriptRoot 'setup_windows.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Setup failed. Read the message above.' }
}
& '.\.venv\Scripts\python.exe' scripts/local_config.py
if ($LASTEXITCODE -ne 0) { throw 'Configuration failed.' }
& '.\.venv\Scripts\python.exe' scripts/check_runtime.py --configured
if ($LASTEXITCODE -ne 0) { throw 'Runtime check failed. Rerun setup.' }
$env:PYTHONUTF8 = '1'
Write-Host 'Open http://127.0.0.1:8001 | Admin ID: admin | Password: 001'
& '.\.venv\Scripts\python.exe' -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
if ($LASTEXITCODE -ne 0) { throw 'Server stopped with an error. Check the output above.' }
