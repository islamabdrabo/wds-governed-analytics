@echo off
setlocal
cd /d %~dp0

set "PORT=8501"
set "APP=app\unified_app.py"

if exist ".venv\Scripts\python.exe" (
  set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
  where py >nul 2>&1
  if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
  ) else (
    set "PYTHON_CMD=python"
  )
)

echo Starting WDS on http://127.0.0.1:%PORT%
call %PYTHON_CMD% -m streamlit run %APP% ^
  --server.headless=true ^
  --server.port=%PORT% ^
  --server.address=127.0.0.1 ^
  --browser.gatherUsageStats=false

endlocal
pause
