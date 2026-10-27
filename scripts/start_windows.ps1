param([ValidateRange(1,65535)][int]$Port = 8001)
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (-not (Test-Path '.venv/Scripts/python.exe') -or -not (Test-Path 'frontend/dist/index.html')) {
    Write-Host "First run: installing this device environment and building the website."
    & (Join-Path $PSScriptRoot 'setup_windows.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Setup failed. Read the message above.' }
} else {
    Push-Location frontend
    try {
        corepack pnpm install --frozen-lockfile
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
        corepack pnpm build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
}
& '.\.venv\Scripts\python.exe' scripts/local_config.py
if ($LASTEXITCODE -ne 0) { throw 'Configuration failed.' }
& '.\.venv\Scripts\python.exe' scripts/check_runtime.py --configured
if ($LASTEXITCODE -ne 0) { throw 'Runtime check failed. Rerun setup.' }
$env:PYTHONUTF8 = '1'
& '.\.venv\Scripts\python.exe' scripts/launch_app.py --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Server stopped with an error. Check the output above.' }
