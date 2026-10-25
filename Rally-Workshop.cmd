@echo off
cd /d "%~dp0"
if not exist ".research-output\rally-workshop\bin\mr-vehicle-previewer.exe" (
  python.exe tools\build_rally_workshop.py
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
pythonw.exe tools\rally_workshop.py %*
if errorlevel 1 pause
