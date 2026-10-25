@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0runtime\pythonw.exe" (
  echo Please extract the entire ZIP before opening Frame Lab.
  pause
  exit /b 1
)
start "" "%~dp0runtime\pythonw.exe" "%~dp0launch.py"
exit /b 0
