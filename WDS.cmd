@echo off
setlocal
cd /d %~dp0

set "PORT=8501"
set "APP=app\unified_app.py"

if exist ".venv\Scripts\pythonw.exe" (
  set "PYTHONW=.venv\Scripts\pythonw.exe"
) else (
  where pythonw >nul 2>&1
  if %errorlevel%==0 (
    set "PYTHONW=pythonw"
  ) else (
    set "PYTHONW=python"
  )
)

start "" %PYTHONW% -m streamlit run %APP% ^
  --server.headless=true ^
  --server.port=%PORT% ^
  --server.address=127.0.0.1 ^
  --browser.gatherUsageStats=false

timeout /t 3 >nul
start "" http://127.0.0.1:%PORT%

endlocal
