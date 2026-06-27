@echo off
cd /d "%~dp0"
python desktop_client.py > mulcat-start.log 2>&1
if errorlevel 1 pause
