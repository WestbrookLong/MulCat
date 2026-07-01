@echo off
cd /d "%~dp0\.."
set MULCAT_UI_DEV_URL=
python -m windows.main
echo.
echo MulCat exited with code %errorlevel%.
pause

