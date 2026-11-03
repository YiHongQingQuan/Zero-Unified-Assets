@echo off
rem ===========================================================================
rem  LaTeX2Word launcher
rem
rem  ASCII only: cmd.exe parses .cmd files with the OEM code page. All Chinese
rem  messages come from Python (bootstrap.py) or from the PowerShell picker.
rem
rem  Usage:
rem     start.cmd                normal start
rem     start.cmd 8765           start on a specific port
rem     start.cmd --select       re-scan and choose the interpreter again
rem     start.cmd --python PATH  use PATH and remember it
rem ===========================================================================
chcp 65001 >nul
cd /d "%~dp0"
setlocal EnableDelayedExpansion

rem %~dp0 must be captured before any shift: shift rewrites %0.
set "SELF_DIR=%~dp0"
if "%SELF_DIR:~-1%"=="\" set "SELF_DIR=%SELF_DIR:~0,-1%"

set "PASSTHRU="
set "FORCE="

:parse
if "%~1"=="" goto run
if /i "%~1"=="--select" goto opt_select
if /i "%~1"=="--python" goto opt_python
set "PASSTHRU=!PASSTHRU! %1"
shift
goto parse

:opt_select
set "FORCE=1"
shift
goto parse

:opt_python
shift
set "LATEX2WORD_PYTHON=%~1"
shift
goto parse

:run
set "CHOOSEFLAG="
if defined FORCE set "CHOOSEFLAG=--choose"
call "!SELF_DIR!\scripts\find-python.cmd" !CHOOSEFLAG!
if errorlevel 2 goto no_python
if errorlevel 1 goto failed
if not defined L2W_PY goto failed

"%L2W_PY%" -X utf8 "!SELF_DIR!\bootstrap.py" !PASSTHRU!
if errorlevel 1 goto failed
exit /b 0

:no_python
echo.
echo ============================================================
echo  No Python 3.10+ interpreter found.
echo ------------------------------------------------------------
echo  Install it from  https://www.python.org/downloads/
echo  or write the full path of python.exe into python.txt
echo ============================================================
echo.
pause
exit /b 2

:failed
echo.
echo LaTeX2Word did not start. See the messages above.
echo.
pause
exit /b 1
