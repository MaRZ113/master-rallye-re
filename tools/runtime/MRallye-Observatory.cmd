@echo off
setlocal
py -3 -c "import sys; ok = sys.version_info >= (3, 11); print('Master Rallye Observatory requires Python 3.11 or newer.') if not ok else None; sys.exit(0 if ok else 2)"
if errorlevel 1 (
    echo Install Python 3.11 or newer with the Windows Python launcher.
    pause
    exit /b 2
)
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
