#!/bin/bash

# Stats-Blender Launch Script (Mac/Linux)

echo "Starting Stats-Blender..."

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install it."
    exit
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install requirements
echo "Checking dependencies..."
source venv/bin/activate
pip install -r backend/requirements.txt --quiet

# Check for .env file
if [ ! -f "backend/.env" ]; then
    if [ -f ".env" ]; then
        cp .env backend/.env
    elif [ -f ".env.example" ]; then
        echo "WARNING: .env file missing. Copying .env.example to backend/.env"
        cp .env.example backend/.env
        echo "Please edit backend/.env with your Spotify API credentials."
    fi
fi

# Run the app
echo "Launching server..."
cd backend
python3 app.py &

# Wait a second for server to start
sleep 2

# Open browser
echo "Opening browser at http://127.0.0.1:8000"
open http://127.0.0.1:8000 || xdg-open http://127.0.0.1:8000 || echo "Please go to http://127.0.0.1:8000 in your browser"

echo "App is running! Press Ctrl+C in this terminal to stop (you might need to kill the process manually if it stays in background)."
wait
