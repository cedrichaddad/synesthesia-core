from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import io
from pydub import AudioSegment
import synesthesia.core as rust_core
from .vector import VectorEngine
from .spotify import SpotifyClient
import hashlib
import uuid
import time
from qdrant_client.http import models
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize engines on startup
    print("Initializing engines...")
    app.state.vector_engine = VectorEngine()
    app.state.spotify_client = SpotifyClient()
    yield
    # Clean up resources if needed
    print("Shutting down engines...")

app = FastAPI(title="Synesthesia API", lifespan=lifespan)

# CORS Configuration
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class KnobRequest(BaseModel):
    current_song_id: str
    knobs: dict[str, float] # knob_name -> value (-1.0 to 1.0)

class RecommendationResponse(BaseModel):
    songs: List[dict]
    vector: List[float]

class SearchResponse(BaseModel):
    song_id: str
    metadata: dict
    vector: List[float]

@app.get("/search", response_model=SearchResponse)
def search(query: str, request: Request):
    try:
        spotify_client = request.app.state.spotify_client
        vector_engine = request.app.state.vector_engine
        
        # Search Spotify
        result = spotify_client.search(query)
        if not result:
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Generate deterministic UUID using same logic as ingest.py
        # This ensures the UUID matches what's stored in Qdrant
        prompt = f"A {result.get('genre', 'unknown')} track by {result['artist']} titled {result['title']}"
        song_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, prompt))
        
        # Get vector using the UUID
        vector = vector_engine.get_vector(song_uuid)
        if vector is None:
            # Fallback: Generate vector on the fly
            print(f"Vector not found for {song_uuid}. Generating on the fly...")
            vector = vector_engine.get_concept_vector(prompt)
            
            # Upsert to Qdrant so it exists for future /recommend calls
            point = models.PointStruct(
                id=song_uuid,
                vector=vector.tolist(),
                payload={
                    "spotify_id": result['id'],
                    "artist": result['artist'],
                    "title": result['title'],
                    "genre": result.get('genre', 'Unknown'),
                    "prompt": prompt,
                    "ingested_at": time.time()
                }
            )
            vector_engine.qdrant.upsert(
                collection_name=vector_engine.collection_name,
                points=[point]
            )
            print(f"Upserted missing track {song_uuid} to Qdrant.")
        
        # Add the UUID to metadata for frontend use
        result['id'] = song_uuid
        
        return SearchResponse(
            song_id=song_uuid,
            metadata=result,
            vector=vector.tolist()
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/suggest")
def suggest(query: str, request: Request):
    """Typeahead suggestions for search"""
    try:
        spotify_client = request.app.state.spotify_client
        results = spotify_client.search_tracks(query, limit=5)
        return {"suggestions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Synchronous 'def' to run in thread pool
@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request_body: KnobRequest, request: Request):
    try:
        vector_engine = request.app.state.vector_engine
        spotify_client = request.app.state.spotify_client
        
        # 1. Get current vector
        current_vector = vector_engine.get_vector(request_body.current_song_id)
        
        # 2. Calculate modification vector
        modification_vector = np.zeros_like(current_vector)
        
        for knob_name, value in request_body.knobs.items():
            # Get concept vector (e.g., "Drums")
            concept_vector = vector_engine.get_concept_vector(knob_name)
            if concept_vector is not None:
                 modification_vector += (value * concept_vector)
        
        # 3. Calculate target
        # V_target = V_current + modification_vector
        target_vector = current_vector + modification_vector
        
        # 4. Normalize
        norm = np.linalg.norm(target_vector)
        if norm > 0:
            target_vector = target_vector / norm
            
        # 5. Search
        results = vector_engine.search(target_vector)
        
        # 6. Fetch details
        songs = []
        for hit in results:
            payload = hit.get('payload', {})
            spotify_id = payload.get('spotify_id')
            
            if not spotify_id:
                print(f"Warning: No spotify_id in payload for {hit['id']}")
                continue
                
            details = spotify_client.get_track_details(spotify_id)
            # Add coordinates flavor text
            details["coordinates"] = f"Sector {hit['id'][:4].upper()}-{hit['id'][-2:].upper()}"
            songs.append(details)
        
        return {
            "songs": songs,
            "vector": target_vector.tolist()
        }
    except Exception as e:
        print(f"Error in recommend endpoint: {e}")
        raise HTTPException(status_code=502, detail=f"Upstream Service Error: {str(e)}")

@app.post("/identify")
async def identify(file: UploadFile = File(...)):
    try:
        # 1. Read and Decode Audio
        # Use pydub to handle various formats (mp3, wav, etc.)
        # We read from the spooled file directly
        audio = AudioSegment.from_file(file.file)
        
        # 2. Preprocess for Rust Engine
        # Resample to 44.1kHz (as expected by audio.rs) and convert to Mono
        audio = audio.set_frame_rate(44100).set_channels(1)
        
        # Convert to numpy array (int16 or int32 usually)
        samples = np.array(audio.get_array_of_samples())
        
        # Normalize to float32 [-1.0, 1.0]
        if audio.sample_width == 2: # 16-bit
            samples = samples.astype(np.float32) / 32768.0
        elif audio.sample_width == 4: # 32-bit
            samples = samples.astype(np.float32) / 2147483648.0
        elif audio.sample_width == 1: # 8-bit unsigned
            samples = (samples.astype(np.float32) - 128.0) / 128.0
        else:
            # Fallback or error for 24-bit (pydub handles it weirdly sometimes)
            samples = samples.astype(np.float32) / (2**(8*audio.sample_width - 1))

        # 3. Call Rust Core (Zero-Copy via Numpy)
        print(f"Fingerprinting {len(samples)} samples...")
        start_time = time.time()
        fingerprints = rust_core.audio_fingerprint(samples)
        duration = time.time() - start_time
        print(f"Generated {len(fingerprints)} fingerprints in {duration:.4f}s")
        
        # 4. Identification Logic (Mocked Lookup for now)
        # In a real system, we would query a DB with these hashes.
        # For this demo, if we successfully generated fingerprints, we return the "Space Oddity" match
        # to keep the UI flow working, but now it's triggered by REAL audio processing.
        
        if not fingerprints:
            raise HTTPException(status_code=400, detail="Could not extract fingerprints from audio. Audio might be too silent or short.")

        # Simulate a database match
        return {
            "song_id": "72Z17vmmeW25ZuvAB0ge7N", # Space Oddity
            "metadata": {
                "title": "Space Oddity",
                "artist": "David Bowie",
                "genre": "Rock",
                "fingerprint_count": len(fingerprints),
                "processing_time": f"{duration:.4f}s"
            }
        }
    except Exception as e:
        print(f"Error in identify endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
