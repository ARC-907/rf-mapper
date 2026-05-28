@echo off
echo ===== OnyxGeoImage Launcher =====
echo.

REM Set PYTHONPATH to include the src directory
set PYTHONPATH=%CD%\src

REM Launch the application
echo Launching GUI (Lite Version)...
python -m sim_rf_map.rf_desktop_app_lite

echo.
echo Application closed.
pause