from fastapi import FastAPI, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import stats
import database
import os
import shutil
import tempfile
import importer
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

app = FastAPI(
    title="Stats-Blender",
    description="Streaming platforms listening statistics",
    version="3.0.0"
)

# CORS: allow frontend origins (configurable for deployment)
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.getenv("DATABASE_DIR", backend_dir)

# API Routes start here

@app.get("/api/health")
def health_check():
    """Health check endpoint for deployment monitoring"""
    return {"status": "ok"}

@app.get("/api/stats/general")
def get_general(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Returns general statistics (listening time, total plays, etc.)"""
    return stats.get_general_stats(start_date, end_date)

@app.get("/api/top/tracks")
def get_top_tracks(
    limit: int = Query(10, description="Number of tracks shown"),
    param: int = Query(0, description="0 for listening time, 1 for number of streams"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Returns top tracks"""
    df = stats.get_top_tracks(limit, param, start_date, end_date)
    return df.to_dict(orient="records")

@app.get("/api/top/artists")
def get_top_artists(
    limit: int = Query(10, description="Number of artists shown"),
    param: int = Query(0, description="0 for listening time, 1 for number of streams"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Returns top artists"""
    df = stats.get_top_artists(limit, param, start_date, end_date)
    return df.to_dict(orient="records")

@app.get("/api/top/albums")
def get_top_albums(
    limit: int = Query(10, description="Number of albums shown"),
    param: int = Query(0, description="0 for listening time, 1 for number of streams"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Returns top albums"""
    df = stats.get_top_albums(limit, param, start_date, end_date)
    return df.to_dict(orient="records")

@app.get("/api/search")
def search(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(10, description="Max results per category")
):
    """Searches for tracks, artists, and albums"""
    return stats.search(q, limit)

@app.get("/api/artist/{name}")
def get_artist_detail(
    name: str,
    limit: int = Query(10, description="Max results"),
    param: int = Query(0, description="0 for listening time, 1 for plays")
):
    """Returns an artist's top tracks and top albums"""
    artist_id = stats.find_artist_id(name)
    if artist_id is None:
        return {"error": "Artist not found", "tracks": [], "albums": []}
    tracks = stats.get_artist_top_tracks(artist_id, limit, param)
    albums = stats.get_artist_top_albums(artist_id, limit, param)
    artist_stats = stats.get_artist_stats(artist_id)
    
    # Fetch image from Spotify
    image_url = None
    try:
        artist_info = sp.artist(artist_id)
        if artist_info['images']:
            image_url = artist_info['images'][0]['url']
    except Exception as e:
        print(f"Spotify API error (artist): {e}")
    
    return {
        "name": name,
        "tracks": tracks.to_dict(orient="records"),
        "albums": albums.to_dict(orient="records"),
        "stats": artist_stats,
        "image_url": image_url
    }

@app.get("/api/album/{name}")
def get_album_detail(
    name: str,
    limit: int = Query(50, description="Max results"),
    param: int = Query(0, description="0 for listening time, 1 for plays")
):
    """Returns an album's tracks"""
    album_id = stats.find_album_id(name)
    if album_id is None:
        return {"error": "Album not found", "tracks": []}
    tracks = stats.get_album_tracks(album_id, limit, param)
    album_stats = stats.get_album_stats(album_id)
    # Get album artist name
    conn = stats.get_connection()
    artist_row = conn.execute("""
        SELECT a.name FROM albums al JOIN artists a ON al.artist_id = a.id WHERE al.id = ?
    """, (album_id,)).fetchone()
    conn.close()
    # Fetch image from Spotify
    image_url = None
    try:
        album_info = sp.album(album_id)
        if album_info['images']:
            image_url = album_info['images'][0]['url']
    except Exception as e:
        print(f"Spotify API error (album): {e}")
        
    return {
        "name": name,
        "artist": artist_row[0] if artist_row else "",
        "tracks": tracks.to_dict(orient="records"),
        "stats": album_stats,
        "image_url": image_url
    }

@app.get("/api/databases")
def list_databases():
    """List all available database files with metadata"""
    import time
    dbs = []
    for f in os.listdir(db_dir):
        if f.endswith(".db"):
            path = os.path.join(db_dir, f)
            stat = os.stat(path)
            dbs.append({
                "name": f,
                "size": stat.st_size,
                "modified": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
            })
    return sorted(dbs, key=lambda x: x['name'])

@app.get("/api/databases/current")
def get_current_database():
    """Returns the name of the currently active database"""
    import database
    return {"current": database.DB_NAME}

@app.post("/api/databases/select")
async def select_database(data: dict):
    """Sets the active database file"""
    name = data.get("name")
    if not name or not name.endswith(".db"):
        return {"error": "Invalid database name"}
    
    db_path = os.path.join(db_dir, name)
    if not os.path.exists(db_path):
        return {"error": "Database file not found"}
    
    database.set_db_name(name)
    return {"success": True, "current": name}

@app.delete("/api/databases/{name}")
def delete_database(name: str):
    """Deletes a database file"""
    if name == database.DB_NAME:
        return {"success": False, "error": "Cannot delete current database"}
    
    db_path = os.path.join(db_dir, name)
    if not os.path.exists(db_path):
        return {"success": False, "error": "Database not found"}
    
    try:
        os.remove(db_path)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/databases/create")
async def create_database(name: str = Form(...), files: List[UploadFile] = File(...)):
    """Creates a new database from uploaded files with real-time progress via streaming"""
    safe_name = name.strip()
    if not safe_name.endswith(".db"):
        safe_name += ".db"
        
    async def generate_progress():
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                for file in files:
                    file_path = os.path.join(temp_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                
                # run_import is a generator
                for progress in importer.run_import(safe_name, temp_dir):
                    yield f"{progress}\n"
                    
            yield f"DONE:{safe_name}\n"
        except Exception as e:
            # Cleanup if failed
            db_path = os.path.join(db_dir, safe_name)
            if os.path.exists(db_path):
                os.remove(db_path)
            yield f"ERROR:{str(e)}\n"

    # Add X-Accel-Buffering: no to prevent PythonAnywhere from buffering the stream
    return StreamingResponse(generate_progress(), media_type="text/plain", headers={"X-Accel-Buffering": "no"})

@app.post("/api/databases/append")
async def append_database(name: str = Form(...), files: List[UploadFile] = File(...)):
    """Appends files to an existing database with real-time progress"""
    if not name.endswith(".db"):
        name += ".db"
        
    db_path = os.path.join(db_dir, name)
    if not os.path.exists(db_path):
        async def err(): yield f"ERROR:Database {name} not found\n"
        return StreamingResponse(err(), media_type="text/plain", headers={"X-Accel-Buffering": "no"})

    async def generate_progress():
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                for file in files:
                    file_path = os.path.join(temp_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                
                # run_import handles everything
                for progress in importer.run_import(name, temp_dir):
                    yield f"{progress}\n"
                    
            yield f"DONE:{name}\n"
        except Exception as e:
            yield f"ERROR:{str(e)}\n"

    return StreamingResponse(generate_progress(), media_type="text/plain", headers={"X-Accel-Buffering": "no"})

# Serve frontend (must be at the end to not shadow /api routes)
frontend_dir = os.path.join(os.path.dirname(backend_dir), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
