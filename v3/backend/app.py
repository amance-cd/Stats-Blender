from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import stats

app = FastAPI(
    title="Stats-Blender",
    description="Streaming platforms listening statistics",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Stats-Blender online. Go to /docs for interactive documentation."}

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

if __name__ == "__main__":
    import uvicorn
    # Lance le serveur API local
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
