import sqlite3
import pandas as pd
from database import DB_NAME

def format_time(ms):
    """Convert ms into Xh XXm format"""
    ms = int(round(ms))
    hours = ms // 3600000  
    minutes = (ms % 3600000) // 60000
    return f"{hours}h {minutes:02d}m"


def get_connection():
    return sqlite3.connect(DB_NAME)

def get_general_stats(start_date=None, end_date=None):
    """Get general stats with optional date filtering """
    conn = get_connection()
    
    #Date filter
    date_filter = ""
    date_filter_p = ""
    params = []
    
    if start_date:
        date_filter += " AND played_at_date >= ?"
        date_filter_p += " AND p.played_at_date >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND played_at_date <= ?"
        date_filter_p += " AND p.played_at_date <= ?"
        params.append(end_date)
        
    params_tuple = tuple(params) 
    
    #Attach date filters to queries
    query_time = f"SELECT SUM(ms_played) FROM plays WHERE 1=1 {date_filter}"
    query_plays = f"SELECT COUNT(track_isrc) FROM plays WHERE 1=1 {date_filter}"
    query_tracks = f"SELECT COUNT(DISTINCT track_isrc) FROM plays WHERE 1=1 {date_filter}"
    
    query_artists = f'''
        SELECT COUNT(DISTINCT a.id) 
        FROM plays p
        JOIN tracks t ON p.track_isrc = t.isrc
        JOIN artists a ON t.artist_id = a.id
        WHERE 1=1 {date_filter_p}
    '''
    
    query_albums = f'''
        SELECT COUNT(DISTINCT t.album_id)
        FROM plays p
        JOIN tracks t ON p.track_isrc = t.isrc
        WHERE 1=1 {date_filter_p}
    '''
    
    #Execute queries
    total_time = conn.execute(query_time, params_tuple).fetchone()[0] or 0
    total_plays = conn.execute(query_plays, params_tuple).fetchone()[0] or 0
    total_tracks = conn.execute(query_tracks, params_tuple).fetchone()[0] or 0
    total_artists = conn.execute(query_artists, params_tuple).fetchone()[0] or 0
    total_albums = conn.execute(query_albums, params_tuple).fetchone()[0] or 0
    
    conn.close()
    
    return {
        "listening_time": format_time(total_time),
        "total_plays": total_plays,
        "total_tracks": total_tracks,
        "total_artists": total_artists,
        "total_albums": total_albums
    }




def order_parameter(param):
    if param == 1:
        return "play_count DESC"
    else:
        return "total_ms DESC"


def get_top_tracks(limit=10, param=0, start_date=None, end_date=None):
    """Get top tracks"""
    conn = get_connection()
    
    #Date filter
    date_filter = ""
    params = []
    if start_date:
        date_filter += " AND p.played_at_date >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND p.played_at_date <= ?"
        params.append(end_date)
    params.append(limit)
    
    query = f'''
        SELECT t.title, a.name as artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN tracks t ON p.track_isrc = t.isrc
        JOIN artists a ON t.artist_id = a.id
        WHERE 1=1 {date_filter}
        GROUP BY p.track_isrc
        ORDER BY {order_parameter(param)}
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=tuple(params))
    conn.close()
    df['listening_time'] = df['total_ms'].apply(format_time)
    return df

def get_top_artists(limit=10, param=0, start_date=None, end_date=None):
    """Get top artists, including featurings"""
    conn = get_connection()
    
    #Date filter
    date_filter = ""
    params = []
    if start_date:
        date_filter += " AND p.played_at_date >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND p.played_at_date <= ?"
        params.append(end_date)
    params.append(limit)
    
    query = f'''
        WITH track_all_artists AS (
            SELECT isrc AS track_isrc, artist_id FROM tracks
            UNION
            SELECT track_isrc, artist_id FROM track_features
        )
        SELECT a.name, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN track_all_artists taa ON p.track_isrc = taa.track_isrc
        JOIN artists a ON taa.artist_id = a.id
        WHERE 1=1 {date_filter}
        GROUP BY a.id
        ORDER BY {order_parameter(param)}
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=tuple(params))
    conn.close()
    df['listening_time'] = df['total_ms'].apply(format_time)
    return df

def get_top_albums(limit=10, param=0, start_date=None, end_date=None):
    """Get top albums"""
    conn = get_connection()
    
    #Date filter
    date_filter = ""
    params = []
    if start_date:
        date_filter += " AND p.played_at_date >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND p.played_at_date <= ?"
        params.append(end_date)
    params.append(limit)
    
    query = f'''
        SELECT al.name as album, a.name as artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN tracks t ON p.track_isrc = t.isrc
        JOIN albums al ON t.album_id = al.id
        JOIN artists a ON al.artist_id = a.id
        WHERE 1=1 {date_filter}
        GROUP BY al.id
        ORDER BY {order_parameter(param)}
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=tuple(params))
    conn.close()
    df['listening_time'] = df['total_ms'].apply(format_time)
    return df

def get_artist_top_tracks(artist_id, limit=10, param=0, start_date=None, end_date=None):
    """Get top tracks of an artist, including featurings"""
    conn = get_connection()

    #Date filter
    date_filter = ""
    params = [artist_id]
    if start_date:
        date_filter += " AND p.played_at_date >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND p.played_at_date <= ?"
        params.append(end_date)
    params.append(limit)

    query = f'''
        WITH track_all_artists AS (
            SELECT isrc AS track_isrc, artist_id FROM tracks
            UNION
            SELECT track_isrc, artist_id FROM track_features
        )
        SELECT t.title, al.name as album, a.name as artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN track_all_artists taa ON p.track_isrc = taa.track_isrc
        JOIN tracks t ON p.track_isrc = t.isrc
        JOIN albums al ON t.album_id = al.id
        JOIN artists a ON taa.artist_id = a.id
        WHERE a.id = ? {date_filter}
        GROUP BY p.track_isrc
        ORDER BY {order_parameter(param)}
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=(artist_id, limit))
    conn.close()
    df['listening_time'] = df['total_ms'].apply(format_time)
    return df

def get_artist_top_albums(artist_id, limit=10, param=0):
    """Get top albums of an artist, including featurings"""
    conn = get_connection()
    query = f'''
        WITH track_all_artists AS (
            SELECT isrc AS track_isrc, artist_id FROM tracks
            UNION
            SELECT track_isrc, artist_id FROM track_features
        )
        SELECT al.name as album, a.name as artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN track_all_artists taa ON p.track_isrc = taa.track_isrc
        JOIN tracks t ON p.track_isrc = t.isrc
        JOIN albums al ON t.album_id = al.id
        JOIN artists a ON taa.artist_id = a.id
        WHERE a.id = ?
        GROUP BY al.id
        ORDER BY {order_parameter(param)}
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=(artist_id, limit))
    conn.close()
    df['listening_time'] = df['total_ms'].apply(format_time)
    return df

def get_album_tracks(album_id, limit=10, param=0):
    """Get top tracks of an album"""
    conn = get_connection()
    query = f'''
        WITH track_all_artists AS (
            SELECT isrc AS track_isrc, artist_id FROM tracks
            UNION
            SELECT track_isrc, artist_id FROM track_features
        )
        SELECT t.title, al.name as album, a.name as artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN track_all_artists taa ON p.track_isrc = taa.track_isrc
        JOIN tracks t ON p.track_isrc = t.isrc
        JOIN albums al ON t.album_id = al.id
        JOIN artists a ON taa.artist_id = a.id
        WHERE al.id = ?
        GROUP BY p.track_isrc
        ORDER BY {order_parameter(param)}
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=(album_id, limit))
    conn.close()
    df['listening_time'] = df['total_ms'].apply(format_time)
    return df


def find_artist_id(name):
    """Find artist id"""
    conn = get_connection()
    result = conn.execute("SELECT id FROM artists WHERE name = ?", (name,)).fetchone()
    conn.close()
    return result[0] if result else None 

def find_album_id(name):
    """Find album id"""
    conn = get_connection()
    result = conn.execute("SELECT id FROM albums WHERE name = ?", (name,)).fetchone()
    conn.close()
    return result[0] if result else None 


if __name__ == "__main__":
    stats = get_general_stats(end_date="2024-01-01")
    print(stats)
