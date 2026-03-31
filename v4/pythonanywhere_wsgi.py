# PythonAnywhere WSGI Configuration
# This file wraps the FastAPI (ASGI) app as WSGI for PythonAnywhere compatibility.
#
# In PythonAnywhere's web app config, set the WSGI file path to this file.
# Update the paths below to match your PythonAnywhere username.

import sys
import os

# IMPORTANT: Replace 'YOUR_USERNAME' with your actual PythonAnywhere username
USERNAME = "YOUR_USERNAME"

# Add the backend directory to the Python path
project_path = f"/home/{USERNAME}/Stats-Blender/v4/backend"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Set environment variables
os.environ["DATABASE_DIR"] = f"/home/{USERNAME}/Stats-Blender/v4/backend"

# Load .env file for Spotify credentials
from dotenv import load_dotenv
load_dotenv(os.path.join(project_path, ".env"))

# Import the FastAPI app and wrap it as WSGI
from app import app as fastapi_app
from a2wsgi import ASGIMiddleware

application = ASGIMiddleware(fastapi_app)
