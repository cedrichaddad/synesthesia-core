import csv
import os
import numpy as np
from typing import List, Callable, Optional
from services.vector import VectorEngine

class Ark:
    def __init__(self, vector_engine: VectorEngine):
        self.vector_engine = vector_engine

    def ingest(self, csv_path: str, batch_size: int = 1000, callback: Optional[Callable[[str], None]] = None):
        """
        Ingest the Ark (tracks_features.csv) into Qdrant.
        """
        def log(msg):
            if callback:
                callback(msg)

        if not os.path.exists(csv_path):
            log(f"Ark file not found: {csv_path}")
            return

        log(f"Opening Ark: {csv_path}")
        
        batch_tracks = []
        batch_vectors = []
        count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # Extract Features
                        energy = float(row.get('energy', 0.5))
                        valence = float(row.get('valence', 0.5))
                        danceability = float(row.get('danceability', 0.5))
                        acousticness = float(row.get('acousticness', 0.5))
                        instrumentalness = float(row.get('instrumentalness', 0.0))
                        
                        # Construct Vector
                        vector = np.array([
                            energy,
                            valence,
                            danceability,
                            acousticness,
                            instrumentalness
                        ], dtype=np.float32)
                        
                        # Clean up Artist string (remove [' '])
                        artist_raw = row.get('artists', 'Unknown')
                        artist = artist_raw.replace("['", "").replace("']", "").replace("', '", ", ")
                        
                        track = {
                            'id': row.get('id'),
                            'name': row.get('name'),
                            'artist': artist,
                            'genre': 'Unknown',
                            'energy': energy,
                            'valence': valence,
                            'danceability': danceability,
                            'acousticness': acousticness,
                            'instrumentalness': instrumentalness
                        }
                        
                        batch_tracks.append(track)
                        batch_vectors.append(vector)
                        
                        if len(batch_tracks) >= batch_size:
                            self.vector_engine.upsert_batch(batch_tracks, batch_vectors)
                            count += len(batch_tracks)
                            log(f"Ingested {count} tracks...")
                            batch_tracks = []
                            batch_vectors = []
                            
                    except ValueError:
                        continue # Skip bad rows
                        
                # Upsert remaining
                if batch_tracks:
                    self.vector_engine.upsert_batch(batch_tracks, batch_vectors)
                    count += len(batch_tracks)
                    
            log(f"Ark Ingestion Complete. Total Tracks: {count}")
            
        except Exception as e:
            log(f"Error during ingestion: {e}")
