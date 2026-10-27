@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_windows.ps1"
if errorlevel 1 (
  echo CivicFlux could not start. Read the error above. Install Python 3.13, Node 24 and Corepack first.
  pause
  exit /b 1
)
