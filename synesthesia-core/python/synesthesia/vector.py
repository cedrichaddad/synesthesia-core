import numpy as np
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

import json
import os

class VectorEngine:
    def __init__(self):
        print("Initializing Vector Engine (5D Physics Mode)...")
        self.collection_name = "synesthesia_tracks_v1"
        
        # Load Concepts
        try:
            with open(os.path.join(os.path.dirname(__file__), 'concepts.json'), 'r') as f:
                self.concepts = json.load(f)
        except Exception as e:
            print(f"Error loading concepts.json: {e}")
            self.concepts = {"atomic": {}, "compound": {}}

        # Initialize Qdrant
        try:
            print("Attempting to connect to Qdrant server...")
            self.qdrant = QdrantClient(host="localhost", port=6333, timeout=2.0)
            # Test connection
            self.qdrant.get_collections()
            print("Connected to Qdrant server.")
        except Exception as e:
            print(f"Qdrant server not available ({e}). Falling back to local storage.")
            self.qdrant = QdrantClient(path="./qdrant_storage")
        
        # Ensure collection exists with 5 Dimensions
        if not self.qdrant.collection_exists(self.collection_name):
            print(f"Creating 5D collection: {self.collection_name}")
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=5, distance=models.Distance.COSINE),
            )
        print("Vector Engine Ready.")

    def get_vector(self, song_id: str) -> Optional[tuple[np.ndarray, dict]]:
        # Retrieve from Qdrant
        points = self.qdrant.retrieve(
            collection_name=self.collection_name,
            ids=[song_id],
            with_vectors=True,
            with_payload=True
        )
        if points:
            return (
                np.array(points[0].vector, dtype=np.float32),
                points[0].payload
            )
        
        # Fallback for prototype if ID not found
        print(f"Warning: Song ID {song_id} not found in DB.")
        return None

    def get_concept_vector(self, concept: str) -> np.ndarray:
        """
        Look up a concept vector from the loaded JSON.
        Returns a 5D numpy array.
        """
        concept_lower = concept.lower()
        
        # Check Atomic
        if concept_lower in self.concepts.get('atomic', {}):
            return np.array(self.concepts['atomic'][concept_lower], dtype=np.float32)
            
        # Check Compound
        if concept_lower in self.concepts.get('compound', {}):
            return np.array(self.concepts['compound'][concept_lower], dtype=np.float32)
            
        print(f"Warning: Concept '{concept}' not found in definitions. Returning Zero Vector.")
        return np.zeros(5, dtype=np.float32)

    def search(self, vector: np.ndarray, k: int = 5) -> List[dict]:
        # Ensure vector is 5D
        if len(vector) != 5:
            print(f"Error: Search vector has {len(vector)} dimensions, expected 5.")
            return []

        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=vector.tolist(),
            limit=k,
            with_payload=True,
            with_vectors=True
        )
        return [{'id': hit.id, 'payload': hit.payload, 'vector': hit.vector} for hit in results.points]

    def upsert(self, track: dict, vector: np.ndarray):
        """
        Store a track in Qdrant.
        track: Full track object (id, title, artist, genre, etc.)
        vector: 5D numpy array
        """
        if len(vector) != 5:
            print(f"Error: Upsert vector has {len(vector)} dimensions, expected 5.")
            return

        # Generate UUID from Spotify ID to ensure consistency
        # We use the Spotify ID directly if it's a valid UUID, but it's not.
        # So we generate a UUID from it.
        import uuid
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, track['id']))

        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload={
                        "spotify_id": track['id'],
                        "title": track['title'],
                        "artist": track['artist'],
                        "genre": track['genre'],
                        "energy": track.get('energy', 0.5),
                        "valence": track.get('valence', 0.5),
                        "danceability": track.get('danceability', 0.5),
                        "acousticness": track.get('acousticness', 0.5),
                        "instrumentalness": track.get('instrumentalness', 0.0)
                    }
                )
            ]
        )
        print(f"Upserted track: {track['title']}")
    def upsert_batch(self, tracks: List[dict], vectors: List[np.ndarray]):
        """
        Batch upsert tracks into Qdrant.
        """
        if len(tracks) != len(vectors):
            print("Error: Track count and vector count mismatch.")
            return

        points = []
        import uuid
        
        for track, vector in zip(tracks, vectors):
            if len(vector) != 5:
                continue
                
            # Generate UUID from Spotify ID
            # Use the 'id' field from the CSV/Track object
            track_id = track.get('id')
            if not track_id:
                continue
                
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, track_id))
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload={
                        "spotify_id": track_id,
                        "title": track.get('name') or track.get('title'), # Handle CSV 'name' vs API 'title'
                        "artist": track.get('artists') or track.get('artist'), # Handle CSV list vs API string
                        "genre": track.get('genre', 'Unknown'),
                        "energy": track.get('energy', 0.5),
                        "valence": track.get('valence', 0.5),
                        "danceability": track.get('danceability', 0.5),
                        "acousticness": track.get('acousticness', 0.5),
                        "instrumentalness": track.get('instrumentalness', 0.0)
                    }
                )
            )
            
        if points:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"Upserted batch of {len(points)} tracks.")
