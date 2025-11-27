import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from typing import List, Dict, Optional
import numpy as np
from .vector import VectorEngine

class SpotifyClient:
    def __init__(self):
        # Initialize Spotipy with OAuth for user data
        self.mock_mode = False
        
        try:
            client_id = os.getenv("SPOTIPY_CLIENT_ID")
            client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                print("Warning: Spotify credentials not found. Switching to Mock Mode.")
                self.mock_mode = True
                return

            redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:3000/callback")
            
            auth_manager = SpotifyOAuth(
                scope="user-top-read",
                redirect_uri=redirect_uri,
                open_browser=False
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            print(f"Spotify Auth failed ({e}). Switching to Mock Mode.")
            self.mock_mode = True

    def get_initial_tracks(self, limit: int = 50) -> List[Dict]:
        if self.mock_mode:
            print("Mock Mode: Returning dummy tracks.")
            return [
                {
                    "id": f"mock_track_{i}",
                    "artist": f"Mock Artist {i}",
                    "title": f"Mock Song {i}",
                    "genre": "Mock Genre",
                    "energy": 0.5 + (i % 10) * 0.05,
                    "valence": 0.5,
                    "danceability": 0.5,
                    "acousticness": 0.5,
                    "instrumentalness": 0.0
                }
                for i in range(limit)
            ]

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
        Batches artist lookups and audio feature fetches.
        """
        processed_tracks = []
        artist_ids = set()
        track_ids = []
        
        # 1. Collect IDs
        for track in tracks:
            if track:
                if track.get('artists'):
                    artist_ids.add(track['artists'][0]['id'])
                track_ids.append(track['id'])
        
        # 2. Batch Fetch Artist Details
        artist_genre_map = {}
        artist_id_list = list(artist_ids)
        
        for i in range(0, len(artist_id_list), 50):
            chunk = artist_id_list[i:i+50]
            try:
                artists_info = self.sp.artists(chunk)
                for artist in artists_info['artists']:
                    if artist:
                        genres = artist.get('genres', [])
                        artist_genre_map[artist['id']] = genres[0].title() if genres else "Pop"
            except Exception as e:
                print(f"Error fetching artist batch: {e}")

        # 3. Batch Fetch Audio Features - DEPRECATED / REMOVED
        # We no longer fetch features from Spotify. The Ark (Qdrant) provides them.
        # audio_features_map = {}
        
        # 4. Format Tracks
        for track in tracks:
            try:
                if not track: continue
                
                artist_name = "Unknown Artist"
                genre = "Pop"
                
                if track.get('artists'):
                    artist = track['artists'][0]
                    artist_name = artist['name']
                    genre = artist_genre_map.get(artist['id'], "Pop")
                
                # Audio Features are now sourced from The Ark (Qdrant) in api.py
                # We return 0.0 here as placeholders.
                
                processed_tracks.append({
                    "id": track['id'],
                    "artist": artist_name,
                    "title": track['name'],
                    "genre": genre,
                    "energy": 0.0,
                    "valence": 0.0,
                    "danceability": 0.0,
                    "acousticness": 0.0,
                    "instrumentalness": 0.0
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
        if self.mock_mode:
            return {
                "id": "mock_search_result",
                "artist": "Mock Artist",
                "title": query,
                "genre": "Mock Genre",
                "energy": 0.8,
                "valence": 0.5,
                "danceability": 0.6,
                "acousticness": 0.2,
                "instrumentalness": 0.0
            }

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
        if self.mock_mode:
            return [
                {
                    "id": f"mock_search_{i}",
                    "artist": "Mock Artist",
                    "title": f"{query} {i}",
                    "genre": "Mock Genre",
                    "energy": 0.5,
                    "valence": 0.5,
                    "danceability": 0.5,
                    "acousticness": 0.5,
                    "instrumentalness": 0.0
                }
                for i in range(limit)
            ]

        results = self.sp.search(q=query, type='track', limit=limit)
        items = results['tracks']['items']
        return self._process_tracks_bulk(items)



    def get_track_details(self, track_id: str) -> Dict:
        """Fetch details for a single track by ID."""
        if self.mock_mode:
            return {
                "id": track_id,
                "artist": "Mock Artist",
                "title": "Mock Title",
                "genre": "Mock Genre",
                "energy": 0.5,
                "valence": 0.5,
                "danceability": 0.5,
                "acousticness": 0.5,
                "instrumentalness": 0.0
            }

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
