import os
import numpy as np
from typing import List, Optional, Dict
from qdrant_client import QdrantClient, models
import uuid

class VectorEngine:
    def __init__(self, collection_name: str = "synesthesia_tracks_v1"):
        self.collection_name = collection_name
        
        # Load Concept Definitions (if any)
        self.concepts = {"atomic": {}, "compound": {}}

        # Initialize Qdrant
        try:
            self.qdrant = QdrantClient(host="localhost", port=6333, timeout=2.0)
            # Test connection
            self.qdrant.get_collections()
        except Exception:
            # Fallback to local storage
            self.qdrant = QdrantClient(path="./qdrant_storage")
        
        # Ensure collection exists with 5 Dimensions
        if not self.qdrant.collection_exists(self.collection_name):
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=5, distance=models.Distance.COSINE),
            )

    def get_count(self) -> int:
        """Returns the number of points in the collection."""
        try:
            return self.qdrant.count(collection_name=self.collection_name).count
        except Exception:
            return 0

    def get_track_data(self, song_id: str) -> Optional[tuple[np.ndarray, dict]]:
        """
        Retrieve vector and payload for a given song ID.
        Returns (vector, payload) or None if not found.
        """
        # Try direct lookup first (if ID is UUID)
        try:
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
        except Exception:
            pass

        # Try generating UUID from Spotify ID (how we store them)
        try:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, song_id))
            points = self.qdrant.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_vectors=True,
                with_payload=True
            )
            if points:
                return (
                    np.array(points[0].vector, dtype=np.float32),
                    points[0].payload
                )
        except Exception:
            pass
        
        return None

    def get_vector(self, song_id: str) -> Optional[tuple[np.ndarray, dict]]:
        # Deprecated alias for get_track_data
        return self.get_track_data(song_id)

    def search(self, vector: np.ndarray, k: int = 5) -> List[dict]:
        # Ensure vector is 5D
        if len(vector) != 5:
            return []

        try:
            results = self.qdrant.query_points(
                collection_name=self.collection_name,
                query=vector.tolist(),
                limit=k,
                with_payload=True,
                with_vectors=True
            )
            return [{'id': hit.id, 'payload': hit.payload, 'vector': hit.vector} for hit in results.points]
        except Exception as e:
            print(f"Vector Search Error: {e}")
            return []

    def upsert_batch(self, tracks: List[dict], vectors: List[np.ndarray]):
        """
        Batch upsert tracks into Qdrant.
        """
        if len(tracks) != len(vectors):
            return

        points = []
        
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
