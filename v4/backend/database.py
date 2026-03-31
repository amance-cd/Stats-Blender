import sqlite3
import os

DB_NAME = "stats-blender_test.db"

def set_db_name(name: str):
    global DB_NAME
    DB_NAME = name

def get_connection():
    """Opens a connection to the database"""
    #Look for the DB in the same directory as this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Creates the tables if they don't exist"""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS artists (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS albums (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            artist_id TEXT REFERENCES artists(id),
            album_type TEXT
        );

        CREATE TABLE IF NOT EXISTS tracks (
            isrc TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            artist_id TEXT REFERENCES artists(id),
            album_id TEXT REFERENCES albums(id),
            duration_ms INTEGER,
            spotify_id TEXT
        );

        CREATE TABLE IF NOT EXISTS track_features (
            track_isrc TEXT REFERENCES tracks(isrc),
            artist_id TEXT REFERENCES artists(id),
            PRIMARY KEY (track_isrc, artist_id)
        );

        CREATE TABLE IF NOT EXISTS plays (
            track_isrc TEXT REFERENCES tracks(isrc),
            played_at_date TEXT,
            played_at_time TEXT,
            ms_played INTEGER,
            source TEXT
        );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__": #creation test
    init_db()
    print("Database created")