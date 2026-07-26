@echo off
setlocal
cd /d "%~dp0"
title RF Mapper Build and Package
echo =====================================
echo Running RF Mapper Build Process
echo =====================================

set "PY_CMD=python"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import PyInstaller" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=.venv\Scripts\python.exe"
)

REM 1. Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM 2. Build with the maintained full build wrapper (runs the test suite first)
%PY_CMD% build_full.py
if errorlevel 1 (
    echo BUILD FAILED - see logs\build_full.log for details.
    pause
    exit /b 1
)

REM 3. Run the bundling script
%PY_CMD% src\sim_rf_map\build_release.py
if errorlevel 1 (
    echo PACKAGING FAILED.
    pause
    exit /b 1
)

echo.
echo DONE. Release is in \release_build\
pause
