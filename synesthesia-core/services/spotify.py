import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional

class SpotifyClient:
    def __init__(self):
        self.mock_mode = False
        try:
            client_id = os.getenv("SPOTIPY_CLIENT_ID")
            client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                print("Spotify credentials not found. Switching to Mock Mode.")
                self.mock_mode = True
                return

            redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:3000/callback")
            
            auth_manager = SpotifyOAuth(
                scope="user-top-read user-modify-playback-state user-read-playback-state",
                redirect_uri=redirect_uri,
                open_browser=False
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=5)
        except Exception as e:
            print(f"Spotify Auth failed ({e}). Switching to Mock Mode.")
            self.mock_mode = True

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
