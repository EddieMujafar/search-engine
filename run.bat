@echo off
REM SimpleSearch Launcher
REM Uses the virtual environment Python if available

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check for virtual environment
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe search_engine.py %*
) else (
    python search_engine.py %*
)