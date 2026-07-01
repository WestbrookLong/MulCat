@echo off
cd /d "%~dp0\.."
python -m windows.main > mulcat-start.log 2>&1
if errorlevel 1 pause

