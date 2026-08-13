@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 "%~dp0dbtool.py" %*
  exit /b %ERRORLEVEL%
)
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python "%~dp0dbtool.py" %*
  exit /b %ERRORLEVEL%
)
echo ERROR Python was not found. dbtool requires Python 3.10 or newer.
exit /b 127
