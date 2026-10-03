@echo off
setlocal
if exist "%~dp0mr_observe.py" (
    pushd "%~dp0"
    py -3 mr_observe.py %*
) else (
    pushd "%~dp0..\.."
    py -3 tools\runtime\mr_observe.py %*
)
set "observe_exit=%ERRORLEVEL%"
if not "%observe_exit%"=="0" pause
popd
exit /b %observe_exit%
