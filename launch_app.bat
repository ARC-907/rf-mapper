@echo off
setlocal
cd /d "%~dp0"
title RF Mapper
echo ===== RF Mapper Launcher =====
echo.

REM Usage: launch_app.bat [full|lite]   (defaults to full)
set "MODE=%~1"
if "%MODE%"=="" set "MODE=full"

REM Make the source tree importable even without an installed package.
set "PYTHONPATH=%CD%\src"

REM 1) Prefer the project virtual environment when it has the app.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sim_rf_map, numpy" >nul 2>nul
    if not errorlevel 1 (
        echo Launching GUI [%MODE%] with the project virtual environment...
        ".venv\Scripts\python.exe" -m sim_rf_map.main --mode=%MODE%
        goto :finished
    )
)

REM 2) Python launcher.
py -3 -c "import sim_rf_map, numpy" >nul 2>nul
if not errorlevel 1 (
    echo Launching GUI [%MODE%] with the Python launcher...
    py -3 -m sim_rf_map.main --mode=%MODE%
    goto :finished
)

REM 3) python on PATH.
python -c "import sim_rf_map, numpy" >nul 2>nul
if not errorlevel 1 (
    echo Launching GUI [%MODE%] with python on PATH...
    python -m sim_rf_map.main --mode=%MODE%
    goto :finished
)

echo ERROR: No Python installation with RF Mapper's dependencies was found.
echo Run dev_setup_launch.bat once to set up the environment, or install with:
echo     python -m pip install -e ".[dev]"
pause
exit /b 1

:finished
if errorlevel 1 (
    echo.
    echo RF Mapper exited with an error. Recent logs are in the logs\ folder.
    pause
    exit /b 1
)
echo.
echo Application closed.
