import pandas as pd
from database import get_connection, init_db
from api import sp
import glob
import os
import re
import concurrent.futures

#----------------------Spotify-------------------------------------------------------

def load_spotify_history(folder):
    """Reads all Spotify JSON files from a folder"""
    pattern = os.path.join(folder, "Streaming_History_Audio_*.json")
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"No files found in {folder}")
        return pd.DataFrame()
    
    file = [pd.read_json(f) for f in files]
    data = pd.concat(file)
    
    #Columns renaming
    data = data.rename(columns={
        'master_metadata_album_artist_name': 'artist',
        'master_metadata_album_album_name': 'album',
        'master_metadata_track_name': 'title',
        'spotify_track_uri': 'url',
    })
    
    #Timestamp extraction
    data['date'] = data['ts'].str[:10]
    data['time'] = data['ts'].str[11:16]
    
    #Filtering : only keep songs with more than 30s of listing (minimal stream duration), no podcast 
    data = data[data['episode_name'].isna() & (data['ms_played'] >= 30000)]
    
    #Spotify ID extraction
    data['spotify_id'] = data['url'].str.split(':').str[-1]

    print(f"{len(data)} songs loaded from Spotify history\n")
    
    return data[['spotify_id', 'ms_played', 'artist', 'title', 'album', 'date', 'time']]




def spotify_api_and_insert(data):
    """Calls Spotify API to get info not in the history, then inserts the data into the DB"""
    init_db()
    conn = get_connection()
    
    #Get all ids and isrcs already in the DB
    db_ids = {row[0] for row in conn.execute("SELECT spotify_id FROM tracks").fetchall()}
    db_isrcs = {row[0] for row in conn.execute("SELECT isrc FROM tracks").fetchall()}

    #Unique ids not already in the DB
    unique_ids = data['spotify_id'].dropna().unique().tolist()
    unique_ids = [id for id in unique_ids if id not in db_ids]
    print(f"Found {len(unique_ids)} unique ids not already in the DB, making API calls to get further info\n")

    print("Progression : ")
    spotify_to_isrc = {}
    
    #Deduplication logic - detailed in readme
    isrc_winners = {}
    type_score = {"album": 3, "compilation": 2, "single": 1}
    
    j = 0
    #API calls, 50 per 50 (Spotify's API limit)
    for i in range(0, len(unique_ids), 50):
    #for i in range(0, 10):
        batch = unique_ids[i:i+50]
        progress = min(100, round((i + len(batch)) / len(unique_ids) * 100))
        if progress == j:
            print(f"{progress}%\n") #Printing progress for each %
            j += 1
        
        try:
            results = sp.tracks(batch)
        except Exception as e:
            print(f"API Error : {e}")
            continue
        
        for track in results['tracks']:
            if track is None:
                continue
            
            isrc = track['external_ids'].get('isrc') #International Standard Recording Code present for all songs on each streaming platform
            if not isrc:
                continue
                
            spotify_id = track['external_urls']['spotify'][31:]
            spotify_to_isrc[spotify_id] = isrc 
                
            new_type = track['album']['album_type']
            new_tracks_count = track['album']['total_tracks']
            new_score = type_score.get(new_type, 0)
            
            if isrc in isrc_winners:
                old_winner = isrc_winners[isrc]
                old_score = type_score.get(old_winner['album']['album_type'], 0)
                old_tracks_count = old_winner['album']['total_tracks']
                
                if new_score > old_score or (new_score == old_score and new_tracks_count > old_tracks_count):
                    isrc_winners[isrc] = track
            else:
                isrc_winners[isrc] = track

    #Insert data
    print("Insertion des données en base...")
    for isrc, track in isrc_winners.items():
        spotify_id_winner = track['external_urls']['spotify'][31:]
        
        #Main artist
        artist = track['artists'][0]
        conn.execute("INSERT OR IGNORE INTO artists (id, name) VALUES (?, ?)", (artist['id'], artist['name']))
        
        #Album
        album = track['album']
        conn.execute("INSERT OR IGNORE INTO albums (id, name, artist_id, album_type) VALUES (?, ?, ?, ?)", (album['id'], album['name'], artist['id'], album['album_type']))
        
        #Track
        conn.execute("INSERT OR IGNORE INTO tracks (isrc, title, artist_id, album_id, duration_ms, spotify_id) VALUES (?, ?, ?, ?, ?, ?)", (isrc, track['name'], artist['id'], album['id'], track['duration_ms'], spotify_id_winner))
        
        #Featured artists
        if len(track['artists']) > 1:
            for feat_artist in track['artists'][1:]:
                conn.execute("INSERT OR IGNORE INTO artists (id, name) VALUES (?, ?)", (feat_artist['id'], feat_artist['name']))
                conn.execute("INSERT OR IGNORE INTO track_features (track_isrc, artist_id) VALUES (?, ?)", (isrc, feat_artist['id']))
    
    conn.commit()
    print("API calls completed")
    
    #Insert plays
    data_to_insert = data.dropna(subset=['spotify_id'])
    plays_data = [(spotify_to_isrc.get(row['spotify_id']), row['date'], row['time'], row['ms_played'], "Spotify") for _, row in data_to_insert.iterrows()]

    conn.executemany(
        "INSERT INTO plays (track_isrc, played_at_date, played_at_time, ms_played, source) VALUES (?, ?, ?, ?, ?)",
        plays_data)

    conn.commit()
    conn.close()







#------------------------Deezer---------------------------------------------------------------------------------------------------------







def load_deezer_history(file_path):
    """Reads Deezer xlsx file and returns a cleaned DataFrame"""
    data = pd.read_excel(file_path, sheet_name='10_listeningHistory') 
    
    #Columns renaming
    data = data.rename(columns={
        'Artist': 'artist',
        'Album Title': 'album',
        'Song Title': 'title',
        'ISRC': 'isrc',
    })

    #Timestamp extraction
    data['date'] = data['Date'].str[:10]
    data['time'] = data['Date'].str[11:16]
    
    #Convert listening time to ms
    data['ms_played'] = data['Listening Time']*1000

    #Filtering : only keep songs with more than 30s of listing (minimal stream duration)
    data = data[(data['ms_played']>30000)]

    return data[['ms_played', 'artist', 'title', 'isrc', 'album', 'date', 'time']]








def deezer_api_and_insert(data):
    """Calls Spotify API to sync artists and albums ids, then inserts the data into the DB"""
    init_db()
    conn = get_connection()

    #Get all isrcs and the album_type linked to them already in the DB
    db_isrc_info = {}
    rows = conn.execute('''SELECT t.isrc, a.album_type FROM tracks t JOIN albums a ON t.album_id = a.id''').fetchall()
    for isrc, album_type in rows:
        db_isrc_info[isrc] = album_type

    unique_isrcs = data['isrc'].dropna().unique().tolist() #Unique isrcs not already in the DB

    #Filtering which isrcs to search for on Spotify API
    isrcs_to_search = []
    for isrc in unique_isrcs:
        if isrc not in db_isrc_info or db_isrc_info[isrc] != "album": 
            isrcs_to_search.append(isrc)

    print(f"Found {len(isrcs_to_search)} isrcs to search for, making API calls to get further info\n")
    print("Progression : ")
    isrc_winners = {}
    type_score = {"album": 3, "compilation": 2, "single": 1}
    

    def fetch_isrc(isrc): #Multi-threading to speed up API calls
        try:
            results = sp.search(q=f"isrc:{isrc}", type="track", limit=4)
            return isrc, results['tracks']['items'] 
        except Exception as e:
            return isrc, []

    # Parallel API Calls (Limit on 10 workers to prevent extreme automatic Rate Limiting delays...)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(fetch_isrc, isrc): isrc for isrc in isrcs_to_search}
        
        j = 0
        total = len(isrcs_to_search)
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            isrc, items = future.result()
            
            progress = min(100, round((i + 1) / total * 100))
            if progress > j:
                print(f"{progress}%\n") 
                j = progress
                
            if not items:
                continue
                
            best_track = None
            best_score = -1
            best_tracks_count = -1
            
            # Choosing the most appropriate version of the track
            for track in items:
                if track['external_ids'].get('isrc') != isrc: #Checking if the isrcs match
                    continue
                    
                new_type = track['album']['album_type']
                new_tracks_count = track['album']['total_tracks']
                new_score = type_score.get(new_type, 0) 
                
                if new_score > best_score or (new_score == best_score and new_tracks_count > best_tracks_count):
                    best_score = new_score
                    best_tracks_count = new_tracks_count
                    best_track = track
                    
            if best_track:
                if isrc in db_isrc_info:
                    old_score = type_score.get(db_isrc_info[isrc], 0)
                    if best_score > old_score: #Comparing the new version with the one present in the DB
                        isrc_winners[isrc] = best_track
                else: 
                    #The ISRC is new, adding it directly
                    isrc_winners[isrc] = best_track



    #Insert data 
    for isrc, track in isrc_winners.items():
        spotify_id_winner = track['external_urls']['spotify'][31:]
        
        artist = track['artists'][0]
        conn.execute("INSERT OR IGNORE INTO artists (id, name) VALUES (?, ?)", (artist['id'], artist['name']))
        
        album = track['album']
        conn.execute("INSERT OR IGNORE INTO albums (id, name, artist_id, album_type) VALUES (?, ?, ?, ?)", (album['id'], album['name'], artist['id'], album['album_type']))
        
        if isrc in db_isrc_info:
            #Updating the track with the new version
            conn.execute("UPDATE tracks SET album_id = ?, spotify_id = ?, title = ?, duration_ms = ? WHERE isrc = ?", (album['id'], spotify_id_winner, track['name'], track['duration_ms'], isrc))
        else:
            #Inserting new track info
            conn.execute("INSERT OR IGNORE INTO tracks (isrc, title, artist_id, album_id, duration_ms, spotify_id) VALUES (?, ?, ?, ?, ?, ?)", (isrc, track['name'], artist['id'], album['id'], track['duration_ms'], spotify_id_winner))
            
            if len(track['artists']) > 1:
                for feat_artist in track['artists'][1:]:
                    conn.execute("INSERT OR IGNORE INTO artists (id, name) VALUES (?, ?)", (feat_artist['id'], feat_artist['name']))
                    conn.execute("INSERT OR IGNORE INTO track_features (track_isrc, artist_id) VALUES (?, ?)", (isrc, feat_artist['id']))
    
    conn.commit()
    print("Data update completed")


    #Inserting plays
    valid_isrcs = {row[0] for row in conn.execute("SELECT isrc FROM tracks").fetchall()}
    data_to_insert = data.dropna(subset=['isrc'])
    plays_data = [(row['isrc'], row['date'], row['time'], row['ms_played'], "Deezer") for _, row in data_to_insert.iterrows() if row['isrc'] in valid_isrcs]
    conn.executemany("INSERT INTO plays (track_isrc, played_at_date, played_at_time, ms_played, source) VALUES (?, ?, ?, ?, ?)", plays_data)
    conn.commit()
    conn.close()




def deduplicate_albums():
    print("\nPattern Matching - Cleaning up duplicate albums")
    conn = get_connection()
    
    albums = conn.execute("SELECT id, name, artist_id FROM albums").fetchall()
    
    #Grouping albums by artists
    artist_albums = {}
    for album_id, name, artist_id in albums:
        if artist_id not in artist_albums:
            artist_albums[artist_id] = []
        artist_albums[artist_id].append((album_id, name))
        
    #Words that indicate a special edition
    deluxe_words = {
        'expansion', 'deluxe', 'bonus', 'extended', 'edition', 'édition', 'version', 
        'remastered', 'remaster', 'long', 'bed', 
        'epilogue', 'boost', 'réédition', 'anniversary', 'track', 
        'tracks', 'taylors', 'taylor', 'pt', 'part', 'vol', 'volume'}
    
    albums_to_merge = []
    for artist_id, album_list in artist_albums.items():
        if len(album_list) < 2: #No need to make any change if the artist only has one album
            continue
        album_list.sort(key=lambda x: len(x[1]), reverse=True) #Sort albums by length of name, longest first
        merged_ids = set()
        
        for i in range(len(album_list)):
            id, name = album_list[i]
            if id in merged_ids: #Skips albums already merged
                continue
                
            name_lower = name.lower()
            for j in range(i + 1, len(album_list)):
                new_id, new_name = album_list[j]
                if new_id in merged_ids: #Skips albums already merged
                    continue
                    
                new_name_lower = new_name.lower()
                if new_name_lower in name_lower:
                    diff = name_lower.replace(new_name_lower, '', 1)
                    words_in_diff = re.findall(r'[^\W\d_]+', diff)
                    has_special_term = any(word in deluxe_words for word in words_in_diff)
                    if len(words_in_diff) > 0 and not has_special_term:
                        continue
                        
                    is_match = True
                    for w in words_in_diff:
                        if w not in deluxe_words:
                            is_match = False
                            break
                            
                    if is_match:
                        albums_to_merge.append((new_id, id, new_name, name))
                        merged_ids.add(new_id)
                        
    for old_id, master_id, old_name, master_name in albums_to_merge:
        conn.execute("UPDATE tracks SET album_id = ? WHERE album_id = ?", (master_id, old_id))
        conn.execute("DELETE FROM albums WHERE id = ?", (old_id,))
        
    conn.commit()
    conn.close()
    print(f"{len(albums_to_merge)} albums cleaned up")

if __name__ == "__main__":
    import time
    start_time = time.time()
    print("--- DÉBUT DE L'IMPORT ---")
    
    # 1. Import Spotify
    """spotify_folder = "/Users/amancedennery/Downloads/Spotify Extended Streaming History-4"
    print("\n[1/2] Import Spotify en cours...")
    spotify_data = load_spotify_history(spotify_folder)
    if not spotify_data.empty:
        spotify_api_and_insert(spotify_data)"""
        
    # 2. Import Deezer
    # Remplace le chemin ci-dessous par le vrai emplacement de ton fichier Excel
    deezer_file = "/Users/amancedennery/Downloads/deezer-data_2633743962.xlsx" 
    print("\n[2/2] Import Deezer en cours...")
    deezer_data = load_deezer_history(deezer_file)
    if not deezer_data.empty:
        deezer_api_and_insert(deezer_data)
        
    deduplicate_albums()
    
    end_time = time.time()
    minutes = int((end_time - start_time) // 60)
    secondes = int((end_time - start_time) % 60)
    print(f"\n--- IMPORT TERMINÉ AVEC SUCCÈS (en {minutes}m {secondes}s) ---")
