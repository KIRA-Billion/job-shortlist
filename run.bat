@echo off
REM Run a search. Double-click, or run: run.bat   (add --quick for a test, --config <file> for another search)
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run setup.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python find_jobs.py %*
pause
