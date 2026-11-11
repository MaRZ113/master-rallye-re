@echo off
setlocal
set "SDK_ROOT=%~dp0.."
set "SDK_PY=%SDK_ROOT%\.research-output\vehicles\workshop2\qt-env\Scripts\python.exe"
if not exist "%SDK_PY%" (
  echo Qt Workshop environment is missing. Open Vehicle Manager from the legacy Workshop or use vehicle_manager.py CLI.
  pause
  exit /b 1
)
if "%~1"=="" (
  "%SDK_PY%" "%~dp0vehicle_manager.py" --qt
) else (
  "%SDK_PY%" "%~dp0vehicle_manager.py" --qt --game "%~1"
)
