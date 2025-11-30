import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional

class SpotifyClient:
    def __init__(self):
        self.mock_mode = False
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        if not client_id or not client_secret:
            if os.getenv("SYN_ENV") == "DEV":
                print("⚠️  WARNING: Running in MOCK MODE (No Spotify Credentials)")
                self.mock_mode = True
                return
            else:
                raise RuntimeError("FATAL: Spotify Credentials Missing in .env file. Set SYN_ENV=DEV to bypass.")

        try:
            redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:3000/callback")
            
            auth_manager = SpotifyOAuth(
                scope="user-top-read user-modify-playback-state user-read-playback-state",
                redirect_uri=redirect_uri,
                open_browser=False
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=5)
        except Exception as e:
            if os.getenv("SYN_ENV") == "DEV":
                print(f"Spotify Auth failed ({e}). Switching to Mock Mode.")
                self.mock_mode = True
            else:
                # CRITICAL: Do not fail silently in production
                raise RuntimeError(f"Spotify Auth Failed: {e}. Check your credentials or set SYN_ENV=DEV.")

    def play_track(self, track_id: str):
        """Start playback of a track."""
        if self.mock_mode:
            print(f"Mock Play: {track_id}")
            return

        try:
            # Get active device
            devices = self.sp.devices()
            active_device = next((d for d in devices['devices'] if d['is_active']), None)
            
            device_id = active_device['id'] if active_device else None
            
            if not device_id and devices['devices']:
                # Fallback to first available device
                device_id = devices['devices'][0]['id']

            if device_id:
                self.sp.start_playback(device_id=device_id, uris=[f"spotify:track:{track_id}"])
            else:
                print("No active Spotify device found.")
        except Exception as e:
            print(f"Error playing track: {e}")

    def get_current_track(self) -> Optional[Dict]:
        """Get currently playing track info."""
        if self.mock_mode:
            return {
                "id": "mock_id",
                "name": "Mock Song",
                "artists": [{"name": "Mock Artist"}]
            }
            
        try:
            current = self.sp.current_playback()
            if current and current.get('item'):
                return current['item']
        except Exception:
            pass
        return None

    def search(self, query: str) -> Dict:
        if self.mock_mode:
            return {
                "id": "mock_search_result",
                "artist": "Mock Artist",
                "title": query,
                "genre": "Mock Genre"
            }

        try:
            results = self.sp.search(q=query, type='track', limit=1)
            items = results['tracks']['items']
            if not items:
                return {
                    "artist": "Unknown",
                    "title": query,
                    "genre": "Unknown"
                }
            
            track = items[0]
            return {
                "id": track['id'],
                "title": track['name'],
                "artist": track['artists'][0]['name'],
                "genre": "Pop" # Placeholder
            }
        except Exception as e:
            print(f"Search error: {e}")
            return {"title": "Error", "artist": "Error"}

    def get_track_details(self, track_id: str) -> Optional[Dict]:
        """Fetch detailed track info including audio features."""
        if self.mock_mode:
            return {
                "id": track_id,
                "name": "Mock Track",
                "artists": [{"name": "Mock Artist"}],
                "audio_features": {
                    "tempo": 120.0,
                    "energy": 0.8,
                    "valence": 0.5,
                    "danceability": 0.6
                }
            }
            
        try:
            track = self.sp.track(track_id)
            features = self.sp.audio_features([track_id])[0]
            
            return {
                "id": track['id'],
                "name": track['name'],
                "artists": track['artists'],
                "audio_features": features
            }
        except Exception as e:
            print(f"Error fetching track details: {e}")
            return None
