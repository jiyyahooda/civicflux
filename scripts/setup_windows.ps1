$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location (Join-Path $PSScriptRoot '..')
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE). See error above." } }
foreach ($name in @('py', 'node', 'corepack')) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw "Install prerequisite: $name. See README.md." }
}
node -e 'if(parseInt(process.versions.node)<24)process.exit(1)'
Check-Exit
# Keep Windows dependencies separate from a copied Mac .venv.
$environment = Join-Path $PWD '.venv-windows'
$python = Join-Path $environment 'Scripts/python.exe'
$nativeReady = $false
if (Test-Path $python) {
    try {
        $check = & $python -c "import sys; assert sys.version_info[:2] == (3,13); assert sys.platform == 'win32'" 2>&1
        $nativeReady = ($LASTEXITCODE -eq 0)
    } catch { $nativeReady = $false }
}
if (-not $nativeReady) {
    if (Test-Path $environment) {
        $backup = $environment + '-transferred-' + (Get-Date -Format 'yyyyMMddHHmmssfff')
        Move-Item -LiteralPath $environment -Destination $backup
        Write-Host 'Preserved the unusable transferred Windows environment in a timestamped backup.'
    }
    py -3.13 -m venv $environment; Check-Exit
}
& $python -c "import sys; assert sys.version_info[:2] == (3,13); assert sys.platform == 'win32'"; Check-Exit
& $python -m pip install -r requirements-test.txt; Check-Exit
& $python -m pip check; Check-Exit
& $python scripts/check_runtime.py; Check-Exit
& $python scripts/local_config.py; Check-Exit
Push-Location frontend
try {
    corepack pnpm install --force --frozen-lockfile; Check-Exit
    corepack pnpm build; Check-Exit
} finally { Pop-Location }
Write-Host 'Ready. Run scripts/run_windows.ps1 backend and scripts/run_windows.ps1 frontend in separate terminals.'
