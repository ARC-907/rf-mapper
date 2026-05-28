@echo off
echo ===== OnyxGeoImage Development Environment Setup and Launch =====
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11 or newer.
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python 3.11 or newer is required. Your version is:
    python --version
    pause
    exit /b 1
)

REM Check if dev_setup.py exists
if not exist src\sim_rf_map\dev_setup.py (
    echo ERROR: dev_setup.py not found at src\sim_rf_map\dev_setup.py
    echo Please make sure you're running this script from the project root directory.
    pause
    exit /b 1
)

REM Run the dev_setup.py script to set up the environment
echo Setting up development environment...
python src\sim_rf_map\dev_setup.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to set up development environment.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist .venv (
    echo ERROR: Virtual environment not found at .venv
    echo The dev_setup.py script should have created it.
    pause
    exit /b 1
)

REM Activate the virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Set PYTHONPATH to include the src directory
echo Setting PYTHONPATH...
set PYTHONPATH=%CD%\src

REM Launch options menu
:menu
cls
echo.
echo ===== OnyxGeoImage Launch Options =====
echo.
echo 1. Launch GUI (Standard)
echo 2. Launch GUI (Lite Version)
echo 3. Launch GUI (Full Version)
echo 4. Run Flow
echo 5. Run Tests
echo 6. Exit
echo.
set /p choice=Enter your choice (1-6): 

if "%choice%"=="1" (
    echo Launching GUI (Standard)...
    python -m sim_rf_map.rf_desktop_app
    goto menu
) else if "%choice%"=="2" (
    echo Launching GUI (Lite Version)...
    python -m sim_rf_map.rf_desktop_app_lite
    goto menu
) else if "%choice%"=="3" (
    echo Launching GUI (Full Version)...
    python -m sim_rf_map.rf_desktop_app_full
    goto menu
) else if "%choice%"=="4" (
    echo Running Flow...
    python -m sim_rf_map.main
    goto menu
) else if "%choice%"=="5" (
    echo Running Tests...
    pytest
    pause
    goto menu
) else if "%choice%"=="6" (
    echo Exiting...
    deactivate
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    pause
    goto menu
)
