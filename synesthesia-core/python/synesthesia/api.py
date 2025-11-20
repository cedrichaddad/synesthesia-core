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

class KnobRequest(BaseModel):
    current_song_id: str
    knob_name: str
    value: float # -1.0 to 1.0

class RecommendationResponse(BaseModel):
    track_ids: List[str]

class SearchResponse(BaseModel):
    metadata: dict
    song_id: str
    vector: List[float]

def normalize_audio(audio: AudioSegment) -> np.ndarray:
    """
    Normalize audio samples to float32 in range [-1.0, 1.0].
    Raises ValueError for unsupported sample widths.
    """
    samples = np.array(audio.get_array_of_samples())
    
    if audio.sample_width == 2: # 16-bit
        return samples.astype(np.float32) / 32768.0
    elif audio.sample_width == 4: # 32-bit
        return samples.astype(np.float32) / 2147483648.0
    else:
        # Fail safe for unsupported formats (e.g. 24-bit packed, 8-bit)
        raise ValueError(f"Unsupported sample width: {audio.sample_width} bytes. Only 16-bit and 32-bit audio are supported.")

@app.post("/identify")
async def identify_audio(file: UploadFile = File(...)):
    try:
        # 1. Read bytes
        content = await file.read()
        
        # 2. Decode with pydub
        audio = AudioSegment.from_file(io.BytesIO(content))
        
        # 3. Resample to 44.1kHz, Mono
        audio = audio.set_frame_rate(44100).set_channels(1)
        
        # 4. Normalize
        audio_data = normalize_audio(audio)

        # 5. Call Rust engine
        fingerprints = rust_core.audio_fingerprint(audio_data.tolist())
        
        if fingerprints:
            return {
                "song_id": "mock_song_id_123", 
                "fingerprints_count": len(fingerprints),
                "sample_hash": fingerprints[0].hash
            }
        else:
            raise HTTPException(status_code=404, detail="Song not recognized")
            
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error identifying audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Synchronous 'def' to run in thread pool
@app.get("/search", response_model=SearchResponse)
def search(query: str, request: Request):
    try:
        # 1. Real Metadata from Spotify
        metadata = request.app.state.spotify_client.search(query)
        
        # 2. Text Proxy
        prompt = f"A {metadata['genre']} track by {metadata['artist']} titled {metadata['title']}"
        
        # 3. Vectorization
        vector = request.app.state.vector_engine.get_concept_vector(prompt)
        
        # 4. Deterministic ID
        song_id = hashlib.sha256(prompt.encode()).hexdigest()[:12]
        
        # 5. Response
        return {
            "metadata": metadata,
            "song_id": song_id,
            "vector": vector.tolist()
        }
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=502, detail=f"Upstream Service Error: {str(e)}")

# Synchronous 'def' to run in thread pool
@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request_body: KnobRequest, request: Request):
    try:
        vector_engine = request.app.state.vector_engine
        
        # 1. Get current vector
        current_vector = vector_engine.get_vector(request_body.current_song_id)
        
        # 2. Get concept vector (e.g., "Drums")
        concept_vector = vector_engine.get_concept_vector(request_body.knob_name)
        
        # 3. Calculate target
        # V_target = V_current + alpha * V_prompt
        target_vector = current_vector + (request_body.value * concept_vector)
        
        # 4. Normalize
        norm = np.linalg.norm(target_vector)
        if norm > 0:
            target_vector = target_vector / norm
            
        # 5. Search
        results = vector_engine.search(target_vector)
        
        return {"track_ids": results}
    except Exception as e:
        print(f"Error in recommend endpoint: {e}")
        raise HTTPException(status_code=502, detail=f"Upstream Service Error: {str(e)}")
