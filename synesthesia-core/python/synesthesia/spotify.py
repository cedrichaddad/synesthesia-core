import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Optional
import numpy as np
from .vector import VectorEngine

class SpotifyClient:
    def __init__(self):
        # Initialize Spotipy with Client Credentials Flow
        # Expects SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in env
        auth_manager = SpotifyClientCredentials()
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_top_tracks(self, limit: int = 20) -> List[Dict]:
        # Fetch top tracks from a global playlist (e.g., Global Top 50)
        # Playlist ID for Global Top 50: 37i9dQZEVXbMDoHDwVN2tF
        results = self.sp.playlist_tracks("37i9dQZEVXbMDoHDwVN2tF", limit=limit)
        tracks = []
        for item in results['items']:
            track = item['track']
            if track:
                # Fallback genre (Spotify doesn't provide genre per track, only per artist)
                artist_id = track['artists'][0]['id']
                artist_info = self.sp.artist(artist_id)
                genres = artist_info.get('genres', [])
                genre = genres[0] if genres else "Pop" # Default fallback
                
                tracks.append({
                    "artist": track['artists'][0]['name'],
                    "title": track['name'],
                    "genre": genre.title()
                })
        return tracks

    def search(self, query: str) -> Dict:
        results = self.sp.search(q=query, type='track', limit=1)
        items = results['tracks']['items']
        if not items:
            # Return empty/unknown if no results found, but don't suppress actual API errors
            return {
                "artist": "Unknown",
                "title": query,
                "genre": "Unknown"
            }
        
        track = items[0]
        artist_id = track['artists'][0]['id']
        artist_info = self.sp.artist(artist_id)
        genres = artist_info.get('genres', [])
        genre = genres[0] if genres else "Pop"
        
        return {
            "artist": track['artists'][0]['name'],
            "title": track['name'],
            "genre": genre.title()
        }

    def generate_user_profile(self, vector_engine: VectorEngine) -> Dict:
        tracks = self.get_top_tracks()
        vectors = []
        prompts = []
        
        for t in tracks:
            # String Interpolation: "A {genre} song by {artist} titled {track_name}"
            prompt = f"A {t['genre']} song by {t['artist']} titled {t['title']}"
            prompts.append(prompt)
            
            # Generate vector using the engine
            vec = vector_engine.get_concept_vector(prompt)
            vectors.append(vec)
        
        if not vectors:
            centroid = np.zeros(512, dtype=np.float32)
        else:
            centroid = np.mean(vectors, axis=0)
        
        return {
            "user_id": "mock_user",
            "vibe_profile": {
                "centroid_vector": centroid.tolist(),
                "top_concepts": [t['genre'] for t in tracks],
                "prompts": prompts
            }
        }
