@echo off
REM Niam-Bay Jarvis - double-click launcher for Windows.
REM Launches the PowerShell script in a hidden window.
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%SCRIPT_DIR%jarvis.ps1"
