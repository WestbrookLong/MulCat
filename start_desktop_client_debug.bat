@echo off
cd /d "%~dp0"
set MULCAT_UI_DEV_URL=
python desktop_client.py
echo.
echo MulCat exited with code %errorlevel%.
pause
