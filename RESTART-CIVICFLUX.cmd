@echo off
cd /d "%~dp0"
echo Close the running CivicFlux server with Ctrl+C before restarting.
pause
call "%~dp0START-CIVICFLUX.cmd"
