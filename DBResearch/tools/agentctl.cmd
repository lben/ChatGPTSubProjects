@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 "%~dp0agentctl.py" %*
  exit /b %ERRORLEVEL%
)
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python "%~dp0agentctl.py" %*
  exit /b %ERRORLEVEL%
)
echo ERROR Python was not found. The Markdown harness still works, but agentctl requires Python 3.10 or newer.
exit /b 127
