@echo off
REM One-time setup for Windows. Double-click this file, or run: setup.bat
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python not found. Install Python 3.10+ from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  pause
  exit /b 1
)

if not exist .venv (
  echo Creating a private Python environment in .venv ...
  py -m venv .venv
)

echo Installing libraries (takes a minute) ...
.venv\Scripts\python -m pip install -q -U pip
.venv\Scripts\python -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo Install failed. Check your internet connection and run setup.bat again.
  pause
  exit /b 1
)

if not exist config.yaml (
  copy config.example.yaml config.yaml >nul
  echo Created config.yaml from the example.
)
if not exist profile.md (
  copy profile.example.md profile.md >nul
  echo Created profile.md from the example.
)

echo.
echo Setup done. Next:
echo   1. Open config.yaml in Notepad and set your job titles, cities and filters (see README.md).
echo   2. Test run:  run.bat --quick
pause
