import time
import numpy as np
from typing import Optional, Dict
from services.vector import VectorEngine
from services.spotify import SpotifyClient

class Navigation:
    def __init__(self, vector_engine: VectorEngine, spotify_client: SpotifyClient):
        self.ve = vector_engine
        self.sp = spotify_client
        self.last_vector = None
        self.last_search_time = 0
        self.current_track_id = None
        
        # Debounce settings
        self.debounce_ms = 300
        self.threshold = 0.01

    def _vector_dict_to_array(self, vector_dict: Dict[str, float]) -> np.ndarray:
        return np.array([
            vector_dict['energy'],
            vector_dict['valence'],
            vector_dict['danceability'],
            vector_dict['acousticness'],
            vector_dict['instrumentalness']
        ], dtype=np.float32)

    def force_search(self, current_vector: Dict[str, float]) -> Optional[Dict]:
        """Force a search immediately, bypassing debounce."""
        vector_array = self._vector_dict_to_array(current_vector)
        return self._perform_search(vector_array)

    def tick(self, current_vector: Dict[str, float]) -> Optional[Dict]:
        """
        Called every tick (e.g. 100ms).
        Returns a result dict if a search/action occurred, else None.
        """
        vector_array = self._vector_dict_to_array(current_vector)

        # Check for significant change
        if self.last_vector is not None:
            dist = np.linalg.norm(vector_array - self.last_vector)
            if dist < self.threshold:
                return None # No significant change

        # Debounce
        now = time.time() * 1000
        if now - self.last_search_time < self.debounce_ms:
            return None

        self.last_vector = vector_array
        self.last_search_time = now
        
        # print(f"Searching for vector: {vector_array}")
        return self._perform_search(vector_array)

    def _perform_search(self, vector_array: np.ndarray) -> Optional[Dict]:
        results = self.ve.search(vector_array, k=1)
        if results:
            track = results[0]
            track_id = track['payload'].get('spotify_id')
            
            # Calculate actual distance
            found_vector = np.array(track['vector'], dtype=np.float32)
            distance = float(np.linalg.norm(vector_array - found_vector))
            
            # Avoid re-playing same track (unless forced? No, keep check)
            if track_id != self.current_track_id:
                self.current_track_id = track_id
                self.sp.play_track(track_id)
                
            return {
                "type": "found",
                "track": track['payload'],
                "distance": distance
            }
        else:
            return {
                "type": "void"
            }
            
        return None
