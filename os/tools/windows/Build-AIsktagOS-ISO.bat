@echo off
rem Build the AIsktagOS ISO on Windows via WSL 2 (Ubuntu).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-AIsktagOS-ISO.ps1" %*
echo.
pause
