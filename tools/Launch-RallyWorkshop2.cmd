@echo off
setlocal
set "WORKSHOP_ROOT=%~dp0.."
set "WORKSHOP_PY=%WORKSHOP_ROOT%\.research-output\vehicles\workshop2\qt-env\Scripts\python.exe"
if not exist "%WORKSHOP_PY%" (
  echo Optional Qt environment is missing. See docs/sdk/WORKSHOP2_QT_RESULTS.md.
  exit /b 1
)
set "WORKSHOP_VIEWER=%WORKSHOP_ROOT%\.research-output\vehicles\v-tex2\viewer-build\Release\mr-vehicle-previewer.exe"
if not exist "%WORKSHOP_VIEWER%" (
  echo Build the current embedded viewer: python tools/build_vehicle_previewer.py --output .research-output/vehicles/v-tex2/viewer-build
  exit /b 1
)
"%WORKSHOP_PY%" "%WORKSHOP_ROOT%\tools\rally_workshop2.py" --workspace "%WORKSHOP_ROOT%\.research-output\vehicles\workshop2\owner-workspace" --viewer "%WORKSHOP_VIEWER%" %*
