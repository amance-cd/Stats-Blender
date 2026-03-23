import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

# Test : chercher un artiste
"""result = sp.search(q=f"isrc:USIR10211038", type="track", limit=10)
track = sp.track("4kqsT3yDyJr1KZ2AkM9qfD")
print(track)
"""