@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
"<LOCAL_PATH>" daily_paper_curator.py --push >> <LOCAL_PATH> 2>&1
endlocal
