@echo off
echo =====================================
echo Running RF Mapper Build Process
echo =====================================

REM Optional: Upgrade pip
python -m pip install --upgrade pip

REM 1. Install dependencies
pip install -r requirements.txt

REM 2. Clean previous builds
rmdir /s /q dist
rmdir /s /q build

REM 3. Build with the maintained full build wrapper
python build_full.py

REM 4. Run bundling script
python src\sim_rf_map\build_release.py

echo.
echo ✅ DONE. Release is in /release_build/
pause
