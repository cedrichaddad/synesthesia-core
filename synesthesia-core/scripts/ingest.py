import sys
import os
import time
import hashlib
import uuid
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Path Hack (Acceptable for simple scripts, but brittle) ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import models
from qdrant_client.http.exceptions import UnexpectedResponse
from python.synesthesia.vector import VectorEngine
from python.synesthesia.spotify import SpotifyClient

# Constants
BATCH_SIZE = 20
RATE_LIMIT_SLEEP = 0.5

def ingest_playlist():
    logger.info("Initializing engines...")
    try:
        vector_engine = VectorEngine()
        spotify_client = SpotifyClient()
    except Exception as e:
        logger.critical(f"Failed to initialize engines: {e}")
        sys.exit(1)

    logger.info("Fetching top tracks from Spotify...")
    try:
        # Fetch more tracks to make the galaxy interesting
        # Use the new hybrid strategy
        tracks = spotify_client.get_initial_tracks(limit=50) 
    except Exception as e:
        logger.error(f"Failed to fetch tracks: {e}")
        sys.exit(1)

    logger.info(f"Found {len(tracks)} tracks. Starting ingestion...")
    
    points_buffer = []
    total_ingested = 0

    for i, track in enumerate(tracks):
        try:
            # Rate Limit Courtesy
            time.sleep(RATE_LIMIT_SLEEP)
            
            # 1. Generate Metadata Prompt
            # Fallback for missing data to prevent crashes
            artist = track.get('artist', 'Unknown Artist')
            title = track.get('title', 'Unknown Track')
            genre = track.get('genre', 'Pop')
            
            prompt = f"A {genre} track by {artist} titled {title}"
            logger.info(f"Processing [{i+1}/{len(tracks)}]: {title}")
            
            # 2. Generate Vector (Heavy Operation)
            vector = vector_engine.get_concept_vector(prompt)
            
            # 3. Deterministic ID (Crucial for Idempotency)
            # Qdrant requires UUID or unsigned integer
            song_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, prompt))
            
            # 4. Create Point
            point = models.PointStruct(
                id=song_id,
                vector=vector.tolist(),
                payload={
                    "spotify_id": track['id'],
                    "artist": artist,
                    "title": title,
                    "genre": genre,
                    "prompt": prompt,
                    "ingested_at": time.time()
                }
            )
            points_buffer.append(point)

            # 5. Batch Upsert
            if len(points_buffer) >= BATCH_SIZE:
                _upsert_batch(vector_engine, points_buffer)
                total_ingested += len(points_buffer)
                points_buffer = [] # Clear buffer

        except Exception as e:
            logger.warning(f"Skipping track '{track.get('title')}': {e}")
            continue

    # Upsert remaining points
    if points_buffer:
        _upsert_batch(vector_engine, points_buffer)
        total_ingested += len(points_buffer)

    logger.info(f"Ingestion complete! Total tracks indexed: {total_ingested}")

def _upsert_batch(engine: VectorEngine, points: List[models.PointStruct]):
    """Helper to handle batched upserts with error handling."""
    try:
        engine.qdrant.upsert(
            collection_name=engine.collection_name,
            points=points
        )
        logger.info(f"--> Flushed batch of {len(points)} vectors to Qdrant.")
    except UnexpectedResponse as e:
        logger.error(f"Qdrant Error: {e}")
    except Exception as e:
        logger.error(f"Failed to upsert batch: {e}")

if __name__ == "__main__":
    ingest_playlist()