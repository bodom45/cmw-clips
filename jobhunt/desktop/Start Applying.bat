@echo off
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3 is needed. Install it from https://www.python.org/downloads/ then run this again. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe (
  echo First-time setup. This takes a few minutes, once.
  python -m venv .venv && .venv\Scripts\pip install -q --upgrade pip playwright && .venv\Scripts\python -m playwright install chromium || (echo Setup failed. & pause & exit /b 1)
)
echo Getting today's job list...
curl -fsSL https://raw.githubusercontent.com/bodom45/cmw-clips/main/jobhunt/seen.json -o seen.json || echo Couldn't download today's list, using the last one.
.venv\Scripts\python apply_assist.py --min-fit 55
pause
