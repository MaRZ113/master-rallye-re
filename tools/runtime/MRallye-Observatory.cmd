@echo off
setlocal
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 2)" >nul 2>nul
if not errorlevel 1 (
    set "OBS_PY=py -3"
    goto python_ready
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 2)" >nul 2>nul
if errorlevel 1 goto no_python
set "OBS_PY=python"
:python_ready
pushd "%~dp0"
%OBS_PY% "%~dp0mr_observe.py" %*
set "observe_exit=%ERRORLEVEL%"
if not "%observe_exit%"=="0" pause
popd
exit /b %observe_exit%
:no_python
echo Master Rallye Observatory requires Python 3.11 or newer.
pause
exit /b 2
