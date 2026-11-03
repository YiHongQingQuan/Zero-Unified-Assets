@echo off
rem ===========================================================================
rem  find-python.cmd  -  locate a working Python >= 3.10 interpreter
rem
rem  ASCII only on purpose: cmd.exe parses .cmd files with the OEM code page;
rem  non-ASCII text turns into garbage commands. All Chinese UI lives in
rem  picker.ps1 (UTF-8 + BOM) and menu.py (UTF-8).
rem
rem  Exports to the caller:
rem     L2W_PY    absolute path of the chosen interpreter
rem     L2W_VER   x.y.z
rem     L2W_BITS  64 / 32
rem     L2W_N     number of qualified candidates
rem     L2W_ALL   number of candidates probed (qualified or not)
rem     L2W_TMP   temp dir holding the candidate lists
rem
rem  Modes:
rem     (none)           resolve + export      (start.cmd)
rem     --list <file>    enumerate only, write "path|ver|bits|source"
rem     --choose         force the picker even when python.txt is valid
rem
rem  Exit: 0 ok / 1 failed or cancelled / 2 no qualified interpreter
rem ===========================================================================
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

rem %~dp0 must be captured before any shift: shift rewrites %0.
set "SELF_DIR=%~dp0"
if "%SELF_DIR:~-1%"=="\" set "SELF_DIR=%SELF_DIR:~0,-1%"
for %%I in ("%SELF_DIR%\..") do set "ROOT=%%~fI"

set "MODE=start"
set "LIST_ARG="
set "FORCED_CHOOSE=0"

:args
if "%~1"=="" goto args_done
if /i "%~1"=="--list" goto arg_list
if /i "%~1"=="--choose" goto arg_choose
shift
goto args
:arg_list
shift
set "LIST_ARG=%~1"
shift
set "MODE=list"
goto args
:arg_choose
shift
set "FORCED_CHOOSE=1"
goto args
:args_done

set "CFG=%ROOT%\python.txt"
set "VENVCFG=%ROOT%\.venv\pyvenv.cfg"
set "TMPD=%TEMP%\l2w-python"
if not exist "%TMPD%" mkdir "%TMPD%" >nul 2>&1
set "LIST_OK=%TMPD%\candidates.txt"
set "LIST_ALL=%TMPD%\scanned.txt"
set "PROBE_OUT=%TMPD%\probe.out"
set "CHOICE_OUT=%TMPD%\choice.txt"

set "N=0"
set "AN=0"
set "L2W_PY="
set "L2W_VER="
set "L2W_BITS="
set "L2W_N=0"
set "L2W_ALL=0"
set "L2W_TMP=%TMPD%"
set "BEST_I=0"
set "BEST_K=0"
set "SOURCES=%L2W_SOURCES%"
if not defined SOURCES set "SOURCES=env,cfg,venv,py,path,reg,dirs"

del "%LIST_OK%" >nul 2>&1
del "%LIST_ALL%" >nul 2>&1

if "%MODE%"=="list" goto do_enumerate
if "%FORCED_CHOOSE%"=="1" goto do_enumerate

rem ---------------------------------------------------------------------------
rem  Phase 1 - high priority sources
rem ---------------------------------------------------------------------------
call :has_source env
if errorlevel 1 goto p_cfg
if not defined LATEX2WORD_PYTHON goto p_cfg
call :probe_path "%LATEX2WORD_PYTHON%" env
if "!PV_OK!"=="1" goto picked
:p_cfg
call :has_source cfg
if errorlevel 1 goto p_venv
if not exist "%CFG%" goto p_venv
call :first_line "%CFG%"
if not defined CFG_LINE goto p_venv
call :probe_path "!CFG_LINE!" cfg
if "!PV_OK!"=="1" goto picked
echo [LaTeX2Word] python.txt points to an unusable interpreter, ignoring it:
echo               !CFG_LINE!  ^(!PV_NOTE!^)
:p_venv
call :has_source venv
if errorlevel 1 goto do_enumerate
if not exist "%ROOT%\.venv\Scripts\python.exe" goto do_enumerate
call :probe_path "%ROOT%\.venv\Scripts\python.exe" venv
if "!PV_OK!"=="1" goto picked

rem ---------------------------------------------------------------------------
rem  Phase 2 - full enumeration
rem ---------------------------------------------------------------------------
:do_enumerate
call :enumerate

if "%MODE%"=="list" goto finish_list
if "!N!"=="0" goto no_candidates
if "%FORCED_CHOOSE%"=="1" goto choose_flow
if "!N!"=="1" goto auto_single
goto choose_flow

:picked
set "L2W_PY=!PV_EXE!"
set "L2W_VER=!PV_VER!"
set "L2W_BITS=!PV_BITS!"
set "L2W_N=1"
call :append_all "!PV_EXE!" "!PV_VER!" "!PV_BITS!" "!P_SRC!" ""
if not "!P_SRC!"=="cfg" goto finish_ok
goto finish_ok

:auto_single
set "L2W_PY=!C_EXE1!"
set "L2W_VER=!C_VER1!"
set "L2W_BITS=!C_BITS1!"
set "L2W_N=1"
call :write_cfg "!L2W_PY!"
goto finish_ok

:choose_flow
call :choose
if errorlevel 1 goto cancelled
call :probe_path "!CHOSEN!" chosen
if "!PV_OK!"=="0" goto cancelled
set "L2W_PY=!PV_EXE!"
set "L2W_VER=!PV_VER!"
set "L2W_BITS=!PV_BITS!"
set "L2W_N=!N!"
if "!REMEMBER!"=="1" call :write_cfg "!L2W_PY!"
goto finish_ok

rem ---------------------------------------------------------------------------
rem  enumeration
rem ---------------------------------------------------------------------------
:enumerate
call :has_source py
if errorlevel 1 goto e_path
for %%V in (3.16 3.15 3.14 3.13 3.12 3.11 3.10) do call :try_cmd "py -%%V" py
:e_path
call :has_source path
if errorlevel 1 goto e_reg
call :try_cmd "python" path
call :try_cmd "python3" path
for %%V in (3.16 3.15 3.14 3.13 3.12 3.11 3.10) do call :try_cmd "python%%V" path
:e_reg
call :has_source reg
if errorlevel 1 goto e_dirs
for %%K in ("HKLM\SOFTWARE\Python\PythonCore" "HKCU\SOFTWARE\Python\PythonCore" "HKLM\SOFTWARE\WOW6432Node\Python\PythonCore") do call :scan_reg %%K
:e_dirs
call :has_source dirs
if errorlevel 1 goto e_end
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do call :try_path "%%~fD\python.exe" dirs
for /d %%D in ("C:\Python3*") do call :try_path "%%~fD\python.exe" dirs
for /d %%D in ("%ProgramFiles%\Python3*") do call :try_path "%%~fD\python.exe" dirs
call :try_path "%USERPROFILE%\miniconda3\python.exe" dirs
call :try_path "%USERPROFILE%\anaconda3\python.exe" dirs
call :try_path "%LOCALAPPDATA%\miniconda3\python.exe" dirs
call :try_path "%LOCALAPPDATA%\anaconda3\python.exe" dirs
call :try_path "C:\ProgramData\miniconda3\python.exe" dirs
call :try_path "C:\ProgramData\anaconda3\python.exe" dirs
call :try_path "%USERPROFILE%\scoop\apps\python\current\python.exe" dirs
:e_end
exit /b 0

:scan_reg
for /f "delims=" %%K in ('reg query %1 2^>nul ^| findstr /i /c:"HKEY_"') do call :reg_key "%%K\InstallPath"
exit /b 0

:reg_key
for /f "tokens=1,2,*" %%a in ('reg query "%~1" /ve 2^>nul ^| findstr /i "REG_SZ"') do call :reg_hit "%%c"
exit /b 0

:reg_hit
set "IP=%~1"
call :trim_left IP
call :trim_right IP
if not defined IP exit /b 0
if "!IP:~-1!"=="\" set "IP=!IP:~0,-1!"
call :try_path "!IP!\python.exe" registry
exit /b 0

:try_cmd
set "P_CMD=%~1"
set "P_SRC=%~2"
call :probe
call :record "%~2"
exit /b 0

:try_path
if not exist "%~1" exit /b 0
set "P_CMD="%~1""
set "P_SRC=%~2"
call :probe
call :record "%~2"
exit /b 0

:probe_path
set "P_CMD="%~1""
call :probe
set "P_SRC=%~2"
exit /b 0

rem ---------------------------------------------------------------------------
rem  :probe  -  uses P_CMD, fills PV_*
rem ---------------------------------------------------------------------------
:probe
set "PV_OK=0"
set "PV_EXE="
set "PV_VER="
set "PV_BITS="
set "PV_MAJ="
set "PV_MIN="
set "PV_PAT="
set "PV_NOTE="
!P_CMD! -X utf8 -c "import sys;print('L2WOK',sys.version_info[0],sys.version_info[1],sys.version_info[2],64 if sys.maxsize>2**32 else 32,sys.executable)" >"%PROBE_OUT%" 2>nul
if errorlevel 1 goto probe_broken
for /f "tokens=1,2,3,4,5,*" %%a in ('findstr /b "L2WOK" "%PROBE_OUT%"') do call :probe_parse "%%a" "%%b" "%%c" "%%d" "%%e"
if not defined PV_MAJ goto probe_broken
set "PV_VER=!PV_MAJ!.!PV_MIN!.!PV_PAT!"
if !PV_MAJ! GTR 3 goto probe_mods
if !PV_MAJ! LSS 3 goto probe_old
if !PV_MIN! LSS 10 goto probe_old
:probe_mods
!P_CMD! -c "import venv,ensurepip" >nul 2>&1
if errorlevel 1 (
  set "PV_NOTE=no-venv-module"
  goto probe_end
)
set "PV_OK=1"
goto probe_end
:probe_old
set "PV_NOTE=version-too-old"
goto probe_end
:probe_broken
set "PV_NOTE=not-runnable"
:probe_end
exit /b 0

:probe_parse
if /i not "%~1"=="L2WOK" exit /b 0
set "PV_MAJ=%~2"
set "PV_MIN=%~3"
set "PV_PAT=%~4"
set "PV_BITS=%~5"
set "PV_EXE="
for /f "usebackq tokens=5,*" %%x in ("%PROBE_OUT%") do set "PV_EXE=%%y"
exit /b 0

rem ---------------------------------------------------------------------------
rem  :record  -  append to scanned list, and to candidates when PV_OK=1
rem ---------------------------------------------------------------------------
:record
set /a AN+=1
set "A_VER=!PV_VER!"
if not defined A_VER set "A_VER=-"
call :append_all "!PV_EXE!" "!A_VER!" "!PV_BITS!" "%~1" "!PV_NOTE!"
if not "!PV_OK!"=="1" exit /b 0
if not defined PV_EXE set "PV_EXE=!P_CMD!"
set "DUP="
if !N! GEQ 1 for /l %%i in (1,1,!N!) do if not defined DUP if /i "!C_EXE%%i!"=="!PV_EXE!" set "DUP=1"
if defined DUP exit /b 0
set /a N+=1
set "C_EXE!N!=!PV_EXE!"
set "C_VER!N!=!PV_VER!"
set "C_BITS!N!=!PV_BITS!"
set "C_SRC!N!=%~1"
set /a KEY=!PV_MAJ!*10000 + !PV_MIN!*100 + !PV_PAT!
if "!PV_BITS!"=="64" set /a KEY+=1
if !KEY! GTR !BEST_K! set "BEST_K=!KEY!"
>>"%LIST_OK%" echo !PV_EXE!^|!PV_VER!^|!PV_BITS!^|%~1
exit /b 0

:append_all
>>"%LIST_ALL%" echo %~1^|%~2^|%~3^|%~4^|%~5
exit /b 0

:write_cfg
>"%CFG%" echo # chosen by LaTeX2Word - delete this file or run "select python" to change
>>"%CFG%" echo %~1
exit /b 0

rem ---------------------------------------------------------------------------
rem  :choose  -  GUI picker, console menu as fallback
rem ---------------------------------------------------------------------------
:choose
set "CHOSEN="
set "REMEMBER=0"
del "%CHOICE_OUT%" >nul 2>&1
if "%PS_DISABLED%"=="1" goto console_menu
where powershell >nul 2>nul
if errorlevel 1 goto console_menu
powershell -NoProfile -STA -ExecutionPolicy Bypass -File "%ROOT%\scripts\picker.ps1" -List "%LIST_OK%" -Out "%CHOICE_OUT%" -Mode select
if not exist "%CHOICE_OUT%" goto console_menu
goto read_choice

:console_menu
del "%CHOICE_OUT%" >nul 2>&1
set "MENU_PY=!C_EXE1!"
"!MENU_PY!" -X utf8 "%ROOT%\scripts\menu.py" "%LIST_OK%" "%CHOICE_OUT%"
if errorlevel 1 exit /b 1
if not exist "%CHOICE_OUT%" exit /b 1

:read_choice
set "CHOSEN="
set "REMEMBER="
for /f "usebackq delims=" %%L in ("%CHOICE_OUT%") do if not defined CHOSEN set "CHOSEN=%%L"
for /f "usebackq skip=1 delims=" %%L in ("%CHOICE_OUT%") do set "REMEMBER=%%L"
if not defined CHOSEN exit /b 1
if /i "!CHOSEN!"=="CANCEL" exit /b 1
if not defined REMEMBER set "REMEMBER=0"
exit /b 0

rem ---------------------------------------------------------------------------
rem  :ask_missing - nothing qualified, offer browse / download
rem ---------------------------------------------------------------------------
:ask_missing
if "%PS_DISABLED%"=="1" exit /b 1
where powershell >nul 2>nul
if errorlevel 1 exit /b 1
del "%CHOICE_OUT%" >nul 2>&1
powershell -NoProfile -STA -ExecutionPolicy Bypass -File "%ROOT%\scripts\picker.ps1" -List "%LIST_ALL%" -Out "%CHOICE_OUT%" -Mode missing
if not exist "%CHOICE_OUT%" exit /b 1
set "CHOSEN="
for /f "usebackq delims=" %%L in ("%CHOICE_OUT%") do if not defined CHOSEN set "CHOSEN=%%L"
if not defined CHOSEN exit /b 1
if /i "!CHOSEN!"=="CANCEL" exit /b 1
call :probe_path "!CHOSEN!" browse
if not "!PV_OK!"=="1" exit /b 1
call :write_cfg "!PV_EXE!"
set "L2W_PY=!PV_EXE!"
set "L2W_VER=!PV_VER!"
set "L2W_BITS=!PV_BITS!"
exit /b 0

rem ---------------------------------------------------------------------------
rem  helpers
rem ---------------------------------------------------------------------------
:has_source
echo ,%SOURCES%, | findstr /i /c:",%1," >nul
exit /b %errorlevel%

:first_line
set "CFG_LINE="
for /f "usebackq delims=" %%L in ("%~1") do if not defined CFG_LINE call :take_first "%%L"
exit /b 0

:take_first
set "T=%~1"
if not defined T exit /b 0
if "!T:~0,1!"=="#" exit /b 0
set "CFG_LINE=!T!"
exit /b 0

:cfg_value
set "CFG_LINE="
for /f "usebackq tokens=1,2 delims==" %%a in ("%~1") do if not defined CFG_LINE call :take_cfg "%%a" "%%b" "%~2"
exit /b 0

:take_cfg
set "K=%~1"
set "V=%~2"
if not defined V exit /b 0
call :trim_left K
call :trim_left V
if /i not "!K!"=="%~3" exit /b 0
set "CFG_LINE=!V!"
exit /b 0

:trim_left
set "TV=!%~1!"
:trim_loop
if not defined TV exit /b 0
if not "!TV:~0,1!"==" " goto trim_done
set "TV=!TV:~1!"
goto trim_loop
:trim_done
set "%~1=!TV!"
exit /b 0

:trim_right
set "TV=!%~1!"
:trimr_loop
if not defined TV exit /b 0
if not "!TV:~-1!"==" " goto trimr_done
set "TV=!TV:~0,-1!"
goto trimr_loop
:trimr_done
set "%~1=!TV!"
exit /b 0

rem ---------------------------------------------------------------------------
rem  exits
rem ---------------------------------------------------------------------------
:finish_list
if not exist "%LIST_OK%" type nul >"%LIST_OK%"
if defined LIST_ARG copy /y "%LIST_OK%" "%LIST_ARG%" >nul 2>&1
set "L2W_N=!N!"
set "L2W_ALL=!AN!"
endlocal & set "L2W_PY=%L2W_PY%" & set "L2W_VER=%L2W_VER%" & set "L2W_BITS=%L2W_BITS%" & set "L2W_N=%L2W_N%" & set "L2W_ALL=%L2W_ALL%" & set "L2W_TMP=%L2W_TMP%" & exit /b 0

:finish_ok
set "L2W_ALL=!AN!"
endlocal & set "L2W_PY=%L2W_PY%" & set "L2W_VER=%L2W_VER%" & set "L2W_BITS=%L2W_BITS%" & set "L2W_N=%L2W_N%" & set "L2W_ALL=%L2W_ALL%" & set "L2W_TMP=%L2W_TMP%" & exit /b 0

:no_candidates
call :ask_missing
if errorlevel 1 goto no_candidates_final
set "L2W_N=1"
goto finish_ok
:no_candidates_final
endlocal & set "L2W_PY=" & set "L2W_N=0" & set "L2W_ALL=%AN%" & set "L2W_TMP=%TMPD%" & exit /b 2

:cancelled
endlocal & set "L2W_PY=" & set "L2W_N=0" & set "L2W_TMP=%TMPD%" & exit /b 1
