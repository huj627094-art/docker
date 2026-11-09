@echo off
rem Double-click: packs code, .env and all data into podzemka.zip on the Desktop
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pack.ps1"
pause
