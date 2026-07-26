@echo off
setlocal
cd /d "%~dp0"
title RF Mapper Development Environment
echo ===== RF Mapper Development Environment Setup and Launch =====
echo.

REM Locate a base Python 3.11+ to create the venv with.
set "BASE_PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if not errorlevel 1 set "BASE_PY=py -3"
if not defined BASE_PY (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "BASE_PY=python"
)
if not defined BASE_PY (
    echo ERROR: Python 3.11 or newer was not found. Install it from python.org.
    pause
    exit /b 1
)

REM Create the virtual environment if it is missing.
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment at .venv ...
    %BASE_PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment.
        pause
        exit /b 1
    )
)

REM Install the project with dev and build extras if not already present.
".venv\Scripts\python.exe" -c "import sim_rf_map, pytest, PyInstaller, numpy" >nul 2>nul
if errorlevel 1 (
    echo Installing RF Mapper with dev and build extras. This can take a few
    echo minutes on first run - the full geospatial/ML stack is downloaded.
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -e ".[dev,build]"
    if errorlevel 1 (
        echo ERROR: Dependency installation failed. Check your network and retry.
        pause
        exit /b 1
    )
)

:menu
echo.
echo ===== RF Mapper Launch Options =====
echo.
echo 1. Launch GUI (Full Version)
echo 2. Launch GUI (Lite Version)
echo 3. Run environment doctor
echo 4. Run tests
echo 5. Build full distribution
echo 6. Exit
echo.
set /p choice=Enter your choice (1-6):

if "%choice%"=="1" (
    echo Launching GUI - Full...
    ".venv\Scripts\python.exe" -m sim_rf_map.main --mode=full
    goto menu
)
if "%choice%"=="2" (
    echo Launching GUI - Lite...
    ".venv\Scripts\python.exe" -m sim_rf_map.main --mode=lite
    goto menu
)
if "%choice%"=="3" (
    ".venv\Scripts\python.exe" -m sim_rf_map.doctor
    pause
    goto menu
)
if "%choice%"=="4" (
    ".venv\Scripts\python.exe" -m pytest -q
    pause
    goto menu
)
if "%choice%"=="5" (
    ".venv\Scripts\python.exe" build_full.py
    pause
    goto menu
)
if "%choice%"=="6" exit /b 0
echo Invalid choice. Please try again.
goto menu
