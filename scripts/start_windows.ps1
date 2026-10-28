param([ValidateRange(1,65535)][int]$Port = 8001)
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
# Always validate this device's native environment and replace copied Node binaries.
& (Join-Path $PSScriptRoot 'setup_windows.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Setup failed. Read the message above.' }
& '.\.venv-windows\Scripts\python.exe' scripts/local_config.py
if ($LASTEXITCODE -ne 0) { throw 'Configuration failed.' }
& '.\.venv-windows\Scripts\python.exe' scripts/check_runtime.py --configured
if ($LASTEXITCODE -ne 0) { throw 'Runtime check failed. Rerun setup.' }
$env:PYTHONUTF8 = '1'
& '.\.venv-windows\Scripts\python.exe' scripts/launch_app.py --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Server stopped with an error. Check the output above.' }
