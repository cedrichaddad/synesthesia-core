import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from typing import List, Dict, Optional
import numpy as np
from .vector import VectorEngine

class SpotifyClient:
    def __init__(self):
        # Initialize Spotipy with OAuth for user data
        # Expects SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI in env
        # Fallback to Client Credentials if no user auth is needed, but here we want user data eventually.
        # For now, we hardcode the redirect_uri as requested or rely on env.
        # The user asked to USE the specific URL in config.
        
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:3000/callback")
        
        auth_manager = SpotifyOAuth(
            scope="user-top-read",
            redirect_uri=redirect_uri,
            open_browser=False
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_initial_tracks(self, limit: int = 50) -> List[Dict]:
        """
        Hybrid Fetch Strategy:
        1. Try to fetch the current user's top tracks (Personalized).
        2. If that fails (e.g. no auth), fallback to Global Top 50 (Generic).
        """
        raw_tracks = []
        
        # Attempt 1: Personalization
        try:
            print("Attempting to fetch user top tracks...")
            results = self.sp.current_user_top_tracks(limit=limit, time_range='medium_term')
            if results and results['items']:
                print(f"Successfully fetched {len(results['items'])} user top tracks.")
                raw_tracks = results['items']
        except Exception as e:
            print(f"User personalization failed (Auth error or no context): {e}")
            print("Falling back to Global Top 50...")

        # Attempt 2: Global Fallback (if no user tracks found)
        if not raw_tracks:
            try:
                # Playlist ID for Global Top 50: 37i9dQZEVXbMDoHDwVN2tF
                results = self.sp.playlist_tracks("37i9dQZEVXbMDoHDwVN2tF", limit=limit)
                # Unpack playlist items to get the track object
                raw_tracks = [item['track'] for item in results['items'] if item['track']]
            except Exception as e:
                print(f"Global fallback failed: {e}")
                return []

        return self._process_tracks_bulk(raw_tracks)

    def _process_tracks_bulk(self, tracks: List[Dict]) -> List[Dict]:
        """
        Efficiently process a list of raw Spotify track objects.
        Batches artist lookups to avoid N+1 API calls.
        """
        processed_tracks = []
        artist_ids = set()
        
        # 1. Collect all Artist IDs
        for track in tracks:
            if track and track.get('artists'):
                artist_ids.add(track['artists'][0]['id'])
        
        # 2. Batch Fetch Artist Details (Chunked by 50, Spotify limit)
        artist_genre_map = {}
        artist_id_list = list(artist_ids)
        
        for i in range(0, len(artist_id_list), 50):
            chunk = artist_id_list[i:i+50]
            try:
                artists_info = self.sp.artists(chunk)
                for artist in artists_info['artists']:
                    if artist:
                        genres = artist.get('genres', [])
                        # Use first genre or default to Pop
                        artist_genre_map[artist['id']] = genres[0].title() if genres else "Pop"
            except Exception as e:
                print(f"Error fetching artist batch: {e}")
        
        # 3. Format Tracks using the map
        for track in tracks:
            try:
                if not track: continue
                
                artist_name = "Unknown Artist"
                genre = "Pop"
                
                if track.get('artists'):
                    artist = track['artists'][0]
                    artist_name = artist['name']
                    # Lookup genre from our batch-fetched map
                    genre = artist_genre_map.get(artist['id'], "Pop")
                
                processed_tracks.append({
                    "id": track['id'],
                    "artist": artist_name,
                    "title": track['name'],
                    "genre": genre
                })
            except Exception as e:
                print(f"Error formatting track {track.get('name', 'Unknown')}: {e}")
                
        return processed_tracks

    def _format_track(self, track: Dict) -> Dict:
        """
        Helper for single track formatting. 
        WARNING: This performs an API call. Use _process_tracks_bulk for lists.
        """
        return self._process_tracks_bulk([track])[0]

    def get_top_tracks(self, limit: int = 20) -> List[Dict]:
        # Deprecated wrapper for backward compatibility, or just redirect
        return self.get_initial_tracks(limit)

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
        return self._format_track(track)

    def search_tracks(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for tracks and return a list of results."""
        results = self.sp.search(q=query, type='track', limit=limit)
        items = results['tracks']['items']
        tracks = []
        for item in items:
            tracks.append(self._format_track(item))
        return tracks

    def generate_user_profile(self, vector_engine: VectorEngine) -> Dict:
        tracks = self.get_initial_tracks()
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

    def get_track_details(self, track_id: str) -> Dict:
        """Fetch details for a single track by ID."""
        try:
            track = self.sp.track(track_id)
            return self._format_track(track)
        except Exception as e:
            print(f"Error fetching track details for {track_id}: {e}")
            return {
                "id": track_id,
                "artist": "Unknown",
                "title": "Unknown",
                "genre": "Unknown"
            }
