import sqlite3
import pandas as pd
import database

def format_time(ms):
    """Convert ms into Xh XXm format"""
    ms = int(round(ms))
    hours = ms // 3600000  
    minutes = (ms % 3600000) // 60000
    return f"{hours}h {minutes:02d}m"


def get_connection():
    return database.get_connection()

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
        WITH track_artists_concat AS (
            SELECT 
                t.isrc,
                t.title,
                (SELECT GROUP_CONCAT(name, ', ') 
                 FROM (
                     SELECT a1.name FROM artists a1 WHERE a1.id = t.artist_id
                     UNION ALL
                     SELECT a2.name FROM track_features tf JOIN artists a2 ON tf.artist_id = a2.id WHERE tf.track_isrc = t.isrc
                 )) as artist
            FROM tracks t
        )
        SELECT tac.title, tac.artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN track_artists_concat tac ON p.track_isrc = tac.isrc
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
        ),
        track_artists_concat AS (
            SELECT 
                t.isrc,
                t.title,
                t.album_id,
                (SELECT GROUP_CONCAT(name, ', ') 
                 FROM (
                     SELECT a1.name FROM artists a1 WHERE a1.id = t.artist_id
                     UNION ALL
                     SELECT a2.name FROM track_features tf JOIN artists a2 ON tf.artist_id = a2.id WHERE tf.track_isrc = t.isrc
                 )) as artist
            FROM tracks t
        )
        SELECT tac.title, al.name as album, tac.artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN track_all_artists taa ON p.track_isrc = taa.track_isrc
        JOIN track_artists_concat tac ON p.track_isrc = tac.isrc
        JOIN albums al ON tac.album_id = al.id
        WHERE taa.artist_id = ? {date_filter}
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
        WITH track_artists_concat AS (
            SELECT 
                t.isrc,
                t.title,
                t.album_id,
                (SELECT GROUP_CONCAT(name, ', ') 
                 FROM (
                     SELECT a1.name FROM artists a1 WHERE a1.id = t.artist_id
                     UNION ALL
                     SELECT a2.name FROM track_features tf JOIN artists a2 ON tf.artist_id = a2.id WHERE tf.track_isrc = t.isrc
                 )) as artist
            FROM tracks t
        )
        SELECT tac.title, al.name as album, tac.artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM plays p
        JOIN track_artists_concat tac ON p.track_isrc = tac.isrc
        JOIN albums al ON tac.album_id = al.id
        WHERE al.id = ?
        GROUP BY p.track_isrc
        ORDER BY {order_parameter(param)}
        LIMIT ?
    '''
    df = pd.read_sql_query(query, conn, params=(album_id, limit))
    conn.close()
    df['listening_time'] = df['total_ms'].apply(format_time)
    return df


def get_artist_stats(artist_id):
    """Get aggregate stats for a specific artist"""
    conn = get_connection()
    query = '''
        WITH track_all_artists AS (
            SELECT isrc AS track_isrc, artist_id FROM tracks
            UNION
            SELECT track_isrc, artist_id FROM track_features
        )
        SELECT 
            COUNT(p.track_isrc) as total_plays,
            SUM(p.ms_played) as total_ms,
            COUNT(DISTINCT p.track_isrc) as unique_tracks,
            MIN(p.played_at_date) as first_listen
        FROM plays p
        JOIN track_all_artists taa ON p.track_isrc = taa.track_isrc
        WHERE taa.artist_id = ?
    '''
    result = conn.execute(query, (artist_id,)).fetchone()
    conn.close()
    return {
        "total_plays": result[0] or 0,
        "total_ms": result[1] or 0,
        "listening_time": format_time(result[1] or 0),
        "unique_tracks": result[2] or 0,
        "first_listen": result[3] or "N/A"
    }

def get_album_stats(album_id):
    """Get aggregate stats for a specific album"""
    conn = get_connection()
    query = '''
        SELECT 
            COUNT(p.track_isrc) as total_plays,
            SUM(p.ms_played) as total_ms,
            COUNT(DISTINCT p.track_isrc) as unique_tracks,
            MIN(p.played_at_date) as first_listen
        FROM plays p
        JOIN tracks t ON p.track_isrc = t.isrc
        WHERE t.album_id = ?
    '''
    result = conn.execute(query, (album_id,)).fetchone()
    conn.close()
    return {
        "total_plays": result[0] or 0,
        "total_ms": result[1] or 0,
        "listening_time": format_time(result[1] or 0),
        "unique_tracks": result[2] or 0,
        "first_listen": result[3] or "N/A"
    }

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


def search(q, limit=10):
    """Search for tracks, artists, and albums by name (including featurings)"""
    conn = get_connection()
    q_wild = f"%{q}%"
    
    #Tracks: match by title, main artist, featuring artist, or album name
    query_tracks = f'''
        WITH track_artists_concat AS (
            SELECT 
                t.isrc,
                t.title,
                t.album_id,
                (SELECT GROUP_CONCAT(name, ', ') 
                 FROM (
                     SELECT a1.name FROM artists a1 WHERE a1.id = t.artist_id
                     UNION ALL
                     SELECT a2.name FROM track_features tf JOIN artists a2 ON tf.artist_id = a2.id WHERE tf.track_isrc = t.isrc
                 )) as artist
            FROM tracks t
        )
        SELECT tac.title as name, tac.artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM track_artists_concat tac
        LEFT JOIN plays p ON tac.isrc = p.track_isrc
        LEFT JOIN tracks t2 ON tac.isrc = t2.isrc
        LEFT JOIN albums al ON t2.album_id = al.id
        WHERE tac.title LIKE ?
           OR tac.artist LIKE ?
           OR al.name LIKE ?
           OR tac.isrc IN (SELECT tf.track_isrc FROM track_features tf JOIN artists a3 ON tf.artist_id = a3.id WHERE a3.name LIKE ?)
        GROUP BY tac.isrc
        ORDER BY play_count DESC
        LIMIT {limit}
    '''
    df_tracks = pd.read_sql_query(query_tracks, conn, params=(q_wild, q_wild, q_wild, q_wild))
    if not df_tracks.empty:
        df_tracks['total_ms'] = df_tracks['total_ms'].fillna(0)
        df_tracks['listening_time'] = df_tracks['total_ms'].apply(format_time)
    
    #Artists: match by name (includes featuring artists)
    query_artists = f'''
        WITH track_all_artists AS (
            SELECT isrc AS track_isrc, artist_id FROM tracks
            UNION
            SELECT track_isrc, artist_id FROM track_features
        )
        SELECT a.name, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM artists a
        LEFT JOIN track_all_artists taa ON a.id = taa.artist_id
        LEFT JOIN plays p ON taa.track_isrc = p.track_isrc
        WHERE a.name LIKE ?
        GROUP BY a.id
        ORDER BY play_count DESC
        LIMIT {limit}
    '''
    df_artists = pd.read_sql_query(query_artists, conn, params=(q_wild,))
    if not df_artists.empty:
        df_artists['total_ms'] = df_artists['total_ms'].fillna(0)
        df_artists['listening_time'] = df_artists['total_ms'].apply(format_time)
    
    #Albums: match by album name or artist name
    query_albums = f'''
        SELECT al.name as name, a.name as artist, SUM(p.ms_played) as total_ms, COUNT(p.track_isrc) as play_count
        FROM albums al
        JOIN artists a ON al.artist_id = a.id
        LEFT JOIN tracks t ON al.id = t.album_id
        LEFT JOIN plays p ON t.isrc = p.track_isrc
        WHERE al.name LIKE ? OR a.name LIKE ?
        GROUP BY al.id
        ORDER BY play_count DESC
        LIMIT {limit}
    '''
    df_albums = pd.read_sql_query(query_albums, conn, params=(q_wild, q_wild))
    if not df_albums.empty:
        df_albums['total_ms'] = df_albums['total_ms'].fillna(0)
        df_albums['listening_time'] = df_albums['total_ms'].apply(format_time)
        
    conn.close()
    
    return {
        "tracks": df_tracks.to_dict(orient="records") if not df_tracks.empty else [],
        "artists": df_artists.to_dict(orient="records") if not df_artists.empty else [],
        "albums": df_albums.to_dict(orient="records") if not df_albums.empty else []
    }

if __name__ == "__main__":
    stats = get_general_stats(end_date="2024-01-01")
    print(stats)
