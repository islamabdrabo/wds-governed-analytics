@echo off
setlocal
cd /d %~dp0

set "PORT=8501"
if not "%~1"=="" set "PORT=%~1"
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

set "LOCAL_IP="
for /f %%I in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254*' } | Select-Object -First 1 -ExpandProperty IPAddress)"') do set "LOCAL_IP=%%I"

echo.
echo Starting WDS for iPad access...
if defined LOCAL_IP (
  echo Open on iPad: http://%LOCAL_IP%:%PORT%
) else (
  echo Could not detect local IPv4 automatically.
  echo Run ipconfig and use your PC IPv4 with port %PORT%.
)
echo.

call %PYTHON_CMD% -m streamlit run %APP% ^
  --server.headless=true ^
  --server.port=%PORT% ^
  --server.address=0.0.0.0 ^
  --browser.gatherUsageStats=false

endlocal
pause
