@echo off
setlocal
set "CIVICFLUX_RESTART_ROOT=%~dp0"
echo Restarting only this project's CivicFlux server on port 8000...
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; $expected=Join-Path $env:CIVICFLUX_RESTART_ROOT '.venv-windows\Scripts\python.exe'; $processes=@(Get-CimInstance Win32_Process); $servers=@($processes | Where-Object { $_.ExecutablePath -eq $expected -and $_.CommandLine -match 'uvicorn\s+backend\.main:app' -and $_.CommandLine -match '--port\s+8000(\s|$)' }); foreach($server in $servers){ $processes | Where-Object { $_.ParentProcessId -eq $server.ProcessId -and $_.CommandLine -match 'uvicorn\s+backend\.main:app' } | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }; Stop-Process -Id $server.ProcessId -ErrorAction SilentlyContinue }"
if errorlevel 1 (
  echo Could not verify the server process. Close the existing CivicFlux server terminal and run START-CIVICFLUX.cmd.
  pause
  exit /b 1
)
call "%~dp0START-CIVICFLUX.cmd"
