import numpy as np
from typing import List, Optional
import torch
from transformers import ClapModel, ClapProcessor
from qdrant_client import QdrantClient
from qdrant_client.http import models

class VectorEngine:
    def __init__(self):
        print("Initializing Vector Engine...")
        self.collection_name = "synesthesia_tracks"
        # Initialize Qdrant
        # Fail Fast: If Qdrant is not reachable, let it crash.
        self.qdrant = QdrantClient(host="localhost", port=6333)
        
        # Ensure collection exists using proper API
        if not self.qdrant.collection_exists(self.collection_name):
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=512, distance=models.Distance.COSINE),
            )

        # Initialize CLAP model
        print("Loading CLAP model...")
        self.model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
        self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print("Vector Engine Ready.")

    def get_vector(self, song_id: str) -> np.ndarray:
        # Retrieve from Qdrant
        points = self.qdrant.retrieve(
            collection_name=self.collection_name,
            ids=[song_id],
            with_vectors=True
        )
        if points:
            return np.array(points[0].vector, dtype=np.float32)
        
        # Fallback for prototype if ID not found (should not happen in prod)
        print(f"Warning: Song ID {song_id} not found in DB. Returning random vector.")
        return np.random.rand(512).astype(np.float32)

    def get_concept_vector(self, concept: str) -> np.ndarray:
        inputs = self.processor(text=[concept], return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            text_embed = self.model.get_text_features(**inputs)
        
        return text_embed.cpu().numpy().flatten().astype(np.float32)

    def search(self, vector: np.ndarray, k: int = 5) -> List[str]:
        # Use query_points for Qdrant 1.16+
        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=vector.tolist(),
            limit=k
        )
        # query_points returns a QueryResponse object with a 'points' attribute
        return [hit.id for hit in results.points]

