@echo off
rem Double-click: runs start.ps1 bypassing the script execution policy
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
pause
