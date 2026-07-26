@echo off
setlocal
cd /d "%~dp0"
title RF Mapper Full Build
REM Build the full RF Mapper distribution through the maintained Python wrapper.

set "PY_CMD=python"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import PyInstaller" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=.venv\Scripts\python.exe"
)

%PY_CMD% build_full.py %*
if errorlevel 1 (
    echo.
    echo BUILD FAILED - see logs\build_full.log for details.
    pause
    exit /b 1
)
echo.
echo Build complete. Output is in dist\rf-mapper\
pause
