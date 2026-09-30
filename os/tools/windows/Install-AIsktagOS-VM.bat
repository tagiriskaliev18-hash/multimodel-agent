@echo off
rem AIsktagOS VM station: installs VirtualBox, creates the VM and a desktop shortcut.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-AIsktagOS-VM.ps1" %*
echo.
pause
