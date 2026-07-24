@echo off
chcp 65001 >nul
cd /d "%~dp0"
set BUN_JSC_useJIT=0

echo [OK] Claude working directory: %CD%

where claude.cmd >nul 2>nul
if errorlevel 1 (
    echo [ERROR] claude.cmd was not found in PATH.
    echo Start PowerShell here and run: cd /d "%~dp0"
    powershell -NoProfile -Command "Read-Host 'Press Enter to close'"
    exit /b 1
)

call claude.cmd %*
