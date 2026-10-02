@echo off
setlocal
rem Repository launcher. For next-to-game deployment use setup-launcher.
pushd "%~dp0..\.."
py -3 tools\runtime\mr_observe.py %*
set "observe_exit=%ERRORLEVEL%"
if not "%observe_exit%"=="0" pause
popd
exit /b %observe_exit%
