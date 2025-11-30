import threading
import uuid
import numpy as np
from typing import Optional, Dict, List, Tuple
import time

from services.vector import VectorEngine
from services.spotify import SpotifyClient
from services.dsp import DSP
from services.ark import Ark
from services.navigation import Navigation
import synesthesia.core as rust_core

class SystemController:
    def __init__(self):
        # Initialize Services
        self.ve = VectorEngine()
        self.sp = SpotifyClient()
        self.dsp = DSP()
        self.ark = Ark(self.ve)
        self.nav = Navigation(self.ve, self.sp)
        
        # State
        self.ingesting = False

    def start(self):
        """Start background services."""
        self.dsp.start()

    def stop(self):
        """Stop background services."""
        self.dsp.stop()

    def handle_search(self, query: str) -> Dict:
        """
        Unified Search Logic (formerly api.py/search).
        1. Search Spotify
        2. Check Ark (Local DB)
        3. Terraform (Fetch features + Upsert) if missing
        """
        # 1. Search Spotify
        result = self.sp.search(query)
        if not result or result.get('title') == 'Error':
            return {"error": "Song not found on Spotify"}

        # Generate deterministic UUID
        song_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, result['id']))
        
        # 2. Check The Ark
        track_data = self.ve.get_vector(song_uuid)
        
        vector = None
        
        if track_data is None:
            # Uncharted Territory - Terraform!
            print(f"Terraforming {result['title']}...")
            
            # Fetch details + features
            track_details = self.sp.get_track_details(result['id'])
            
            if track_details:
                # Calculate Vector
                vector = np.array([
                    track_details.get('energy', 0.5),
                    track_details.get('valence', 0.5),
                    track_details.get('danceability', 0.5),
                    track_details.get('acousticness', 0.5),
                    track_details.get('instrumentalness', 0.0)
                ], dtype=np.float32)
                
                # Upsert into Qdrant
                self.ve.upsert_batch([track_details], [vector])
                result['coordinates'] = f"Sector {song_uuid[:4].upper()} (Terraformed)"
            else:
                # Fallback
                vector = np.array([0.5, 0.5, 0.5, 0.5, 0.0], dtype=np.float32)
                result['coordinates'] = "Unknown Sector"
        else:
            vector, payload = track_data
            result['coordinates'] = f"Sector {song_uuid[:4].upper()}"
            # Merge payload metadata
            result.update(payload)

        return {
            "song_id": song_uuid,
            "metadata": result,
            "vector": vector
        }

    def handle_ingest(self, callback=None):
        """Run ingestion in a background thread."""
        if self.ingesting:
            return
        
        self.ingesting = True
        def run():
            self.ark.ingest("data/tracks_features.csv", callback=callback)
            self.ingesting = False
            
        threading.Thread(target=run, daemon=True).start()

    def ingest_user_playlist(self, limit: int = 50):
        """Fetch User's Top Tracks and ingest them (Green Nodes)."""
        def run():
            print(f"Fetching top {limit} tracks...")
            tracks = self.sp.get_initial_tracks(limit=limit)
            if not tracks:
                print("No tracks found.")
                return

            count = 0
            for track in tracks:
                vector = np.array([
                    track.get('energy', 0.5),
                    track.get('valence', 0.5),
                    track.get('danceability', 0.5),
                    track.get('acousticness', 0.5),
                    track.get('instrumentalness', 0.0)
                ], dtype=np.float32)
                
                self.ve.upsert(track, vector)
                count += 1
            print(f"Ingested {count} user tracks.")
            
        threading.Thread(target=run, daemon=True).start()

    def handle_suggest(self, query: str) -> List[Dict]:
        """Typeahead suggestions."""
        return self.sp.search_tracks(query, limit=5)

    def tick(self, current_vector: Dict[str, float]) -> Optional[Dict]:
        """Game Loop Tick."""
        return self.nav.tick(current_vector)

    def force_search(self, current_vector: Dict[str, float]) -> Optional[Dict]:
        return self.nav.force_search(current_vector)

    def analyze_audio(self, audio_data: np.ndarray) -> Tuple[List[Tuple[int, int]], float, float]:
        """
        Direct call to Rust Core for analysis.
        Returns (fingerprints, rms, flatness).
        """
        fingerprints = rust_core.audio_fingerprint(audio_data)
        try:
            rms, flatness = rust_core.audio_analyze(audio_data)
        except Exception:
            rms, flatness = 0.0, 0.0
        return fingerprints, rms, flatness
