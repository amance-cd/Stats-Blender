@echo off
title Stats-Blender Launcher

echo Starting Stats-Blender...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Please install Python 3.
    pause
    exit /b
)

:: Create venv if not exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate and install
echo Checking dependencies...
call venv\Scripts\activate
pip install -r backend\requirements.txt --quiet

:: Check .env
if not exist backend\.env (
    if exist .env (
        copy .env backend\.env
    ) else (
        if exist .env.example (
            echo WARNING: .env file missing. Creating from example...
            copy .env.example backend\.env
            echo Please edit backend\.env with your Spotify credentials.
        )
    )
)

:: Run app
echo Launching server...
cd backend
start "" http://127.0.0.1:8000
python app.py

pause
