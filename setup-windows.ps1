# Compatibility entry point: use the same setup as the README and CI.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'scripts/setup_windows.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
