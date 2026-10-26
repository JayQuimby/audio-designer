@echo off
rem Launch Voice Assist from source (Windows). Creates a virtualenv on first run.
cd /d "%~dp0"

rem The venv is only trusted once an install finished with the current requirements.txt (recorded by the
rem copy below). An interrupted or outdated setup is simply rebuilt.
fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if errorlevel 1 (
    echo Setting up (first run only, this can take a few minutes)...
    if exist .venv rmdir /s /q .venv
    py -3 -m venv .venv || (echo Python 3.9 or newer is required. Install it from python.org. & exit /b 1)
    .venv\Scripts\python -m pip install --quiet --upgrade pip
    .venv\Scripts\python -m pip install --quiet -r requirements.txt || exit /b 1
    copy /y requirements.txt .venv\requirements.installed >nul
)

.venv\Scripts\python scripts\fetch_assets.py || exit /b 1
.venv\Scripts\python -m voice_assist
