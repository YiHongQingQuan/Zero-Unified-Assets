@echo off
rem ===========================================================================
rem  Choose which Python LaTeX2Word uses (double-click me).
rem  ASCII only: see start.cmd for the reason.
rem ===========================================================================
chcp 65001 >nul
cd /d "%~dp0"
setlocal EnableDelayedExpansion

set "SELF_DIR=%~dp0"
if "%SELF_DIR:~-1%"=="\" set "SELF_DIR=%SELF_DIR:~0,-1%"

call "!SELF_DIR!\scripts\find-python.cmd" --choose
if errorlevel 1 goto cancelled
if not defined L2W_PY goto cancelled

echo.
echo Selected: !L2W_PY!  ^(!L2W_VER!, !L2W_BITS! bit^)
"%L2W_PY%" -X utf8 "!SELF_DIR!\bootstrap.py" --prepare
if errorlevel 1 goto failed

echo.
echo Done. Run start.cmd to launch LaTeX2Word.
echo.
pause
exit /b 0

:cancelled
echo.
echo Nothing was changed.
echo.
pause
exit /b 1

:failed
echo.
echo Failed to prepare the environment. See the messages above.
echo.
pause
exit /b 1
