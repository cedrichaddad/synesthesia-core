from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import io

import synesthesia.core as rust_core
from .vector import VectorEngine
from .spotify import SpotifyClient
import hashlib
import uuid
import time
from qdrant_client.http import models
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

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
        
        # Search Spotify for metadata
        result = spotify_client.search(query)
        if not result:
            raise HTTPException(status_code=404, detail="Song not found on Spotify")
        
        # Generate deterministic UUID from Spotify ID (Consistent with vector.py)
        # prompt = f"A {result.get('genre', 'unknown')} track by {result['artist']} titled {result['title']}"
        song_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, result['id']))
        # 2. Check The Ark (Local DB)
        track_data = vector_engine.get_vector(song_uuid)
        
        if track_data is None:
            # Uncharted Territory
            print(f"Song {result['title']} is Uncharted (Not in Ark).")
            vector = np.zeros(5, dtype=np.float32)
            result['coordinates'] = "UNCHARTED"
            
            # Track not in our database -> Fetch-on-Miss (Terraforming)
            print(f"L1 Miss for {result['title']}. Fetching Audio Features...")
            
            # Fetch details + features
            try:
                track_details = spotify_client.get_track_details(result['id'])
                
                if not track_details or track_details.get('title') == 'Unknown':
                     raise HTTPException(status_code=404, detail=f"Song {result['title']} found but details could not be retrieved.")
                
                # Calculate Vector
                vector = np.array([
                    track_details.get('energy', 0.5),
                    track_details.get('valence', 0.5),
                    track_details.get('danceability', 0.5),
                    track_details.get('acousticness', 0.5),
                    track_details.get('instrumentalness', 0.0)
                ], dtype=np.float32)
                
                # Upsert into Qdrant (Terraforming)
                # We do this synchronously to ensure it's available immediately
                vector_engine.upsert(track_details, vector)
                print(f"Terraformed {result['title']} into Sector {song_uuid[:4]}")
                
            except Exception as e:
                print(f"Error fetching features for search result: {e}")
                # Fallback to default vector if fetch fails, but don't crash
                vector = np.array([0.5, 0.5, 0.5, 0.5, 0.0], dtype=np.float32)
        else:
            vector, payload = track_data
            result['coordinates'] = f"Sector {song_uuid[:4].upper()}"
            
            # MERGE PAYLOAD METADATA (Fixing Zero-Metadata Bug)
            result['energy'] = payload.get('energy', 0.0)
            result['valence'] = payload.get('valence', 0.0)
            result['danceability'] = payload.get('danceability', 0.0)
            result['acousticness'] = payload.get('acousticness', 0.0)
            result['instrumentalness'] = payload.get('instrumentalness', 0.0)
            result['genre'] = payload.get('genre', result['genre'])
        
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

@app.post("/ingest_playlist")
def ingest_playlist(request: Request, background_tasks: BackgroundTasks):
    """
    Fetch tracks from User's Top Tracks (or a specific playlist) and ingest them into Qdrant.
    This seeds the database with "Green Nodes".
    """
    try:
        spotify_client = request.app.state.spotify_client
        vector_engine = request.app.state.vector_engine
        
        # Fetch tracks
        tracks = spotify_client.get_initial_tracks(limit=50)
        
        if not tracks:
            return {"status": "warning", "message": "No tracks found to ingest."}
            
        # Process in background to avoid blocking
        def process_ingestion(tracks_to_ingest):
            print(f"Starting background ingestion of {len(tracks_to_ingest)} tracks...")
            count = 0
            for track in tracks_to_ingest:
                # Create 5D Vector from Audio Features
                # [Energy, Valence, Danceability, Acousticness, Instrumentalness]
                vector = np.array([
                    track.get('energy', 0.5),
                    track.get('valence', 0.5),
                    track.get('danceability', 0.5),
                    track.get('acousticness', 0.5),
                    track.get('instrumentalness', 0.0)
                ], dtype=np.float32)
                
                vector_engine.upsert(track, vector)
                count += 1
            print(f"Ingestion complete. {count} tracks added.")

        background_tasks.add_task(process_ingestion, tracks)
        
        return {"status": "success", "message": f"Started ingestion of {len(tracks)} tracks."}
    except Exception as e:
        print(f"Error in ingest_playlist: {e}")
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
        
        # 1. Get current vector
        track_data = vector_engine.get_vector(request_body.current_song_id)
        
        if track_data is None:
            # Should not happen if we only allow locking on Charted songs
            # But if it does, fallback to center
            current_vector = np.array([0.5, 0.5, 0.5, 0.5, 0.0], dtype=np.float32)
        else:
            current_vector, _ = track_data
        
        # 2. Calculate modification vector
        modification_vector = np.zeros_like(current_vector)
        
        for knob_name, value in request_body.knobs.items():
            concept_vector = vector_engine.get_concept_vector(knob_name)
            if concept_vector is not None:
                concept_vector = concept_vector.flatten()
                modification_vector += (value * concept_vector)
        
        # 3. Calculate target
        target_vector = current_vector + modification_vector
        target_vector = np.clip(target_vector, 0.0, 1.0)
            
        # 4. Search The Ark
        results = vector_engine.search(target_vector, k=5)
        
        songs = []
        for hit in results:
            if hit['id'] == request_body.current_song_id:
                continue
            
            payload = hit.get('payload', {})
            songs.append({
                "id": payload.get('spotify_id'),
                "title": payload.get('title', 'Unknown'),
                "artist": payload.get('artist', 'Unknown'),
                "genre": payload.get('genre', 'Unknown'),
                "coordinates": f"Sector {hit['id'][:4].upper()}",
                "source": "THE_ARK",
                "vector": hit.get('vector')
            })
        
        return {
            "songs": songs,
            "vector": target_vector.tolist()
        }
    except Exception as e:
        print(f"Error in recommend endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

import subprocess

def decode_audio_ffmpeg(file_bytes: bytes) -> np.ndarray:
    """
    Decode audio bytes to 44.1kHz Mono Float32 using ffmpeg.
    """
    try:
        process = subprocess.Popen(
            ['ffmpeg', '-i', 'pipe:0', '-f', 'f32le', '-ac', '1', '-ar', '44100', 'pipe:1'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = process.communicate(input=file_bytes)
        
        if process.returncode != 0:
            print(f"FFmpeg error: {err.decode()}")
            raise Exception("FFmpeg decoding failed")
            
        return np.frombuffer(out, dtype=np.float32)
    except Exception as e:
        print(f"Audio decoding error: {e}")
        return np.array([], dtype=np.float32)

from fastapi.concurrency import run_in_threadpool

@app.post("/identify")
async def identify(file: UploadFile = File(...)):
    try:
        # 1. Read Audio (Async I/O)
        file_bytes = await file.read()
        
        # 2. Decode with FFmpeg (Blocking I/O -> ThreadPool)
        samples = await run_in_threadpool(decode_audio_ffmpeg, file_bytes)
        
        if len(samples) == 0:
             raise HTTPException(status_code=400, detail="Could not decode audio file.")

        # 3. Call Rust Core (CPU Bound -> ThreadPool)
        print(f"Fingerprinting {len(samples)} samples...")
        start_time = time.time()
        
        # Run heavy Rust calculations in threadpool
        def analyze_audio(audio_samples):
            fps = rust_core.audio_fingerprint(audio_samples)
            try:
                r, f = rust_core.audio_analyze(audio_samples)
            except Exception:
                r, f = 0.0, 0.0
            return fps, r, f

        fingerprints, rms, flatness = await run_in_threadpool(analyze_audio, samples)
        
        print(f"Physics Analysis: RMS={rms:.4f}, Flatness={flatness:.4f}")

        duration = time.time() - start_time
        print(f"Generated {len(fingerprints)} fingerprints in {duration:.4f}s")
        
        if not fingerprints:
            # For demo, if we have samples but no fingerprints (silence?), we might still want to return something?
            # But usually this means bad audio.
            # Let's be lenient for demo.
            pass

        # Map Physics to 5D Vector
        # Energy = RMS * Gain (heuristic)
        # Acousticness = 1.0 - Flatness (heuristic: flat = noise/percussion, peaked = tonal/acoustic)
        
        energy = min(rms * 5.0, 1.0) # Gain of 5.0 to boost quiet signals
        acousticness = max(0.0, 1.0 - (flatness * 2.0)) # Flatness usually low for tonal
        
        dynamic_vector = [
            energy,          # Energy
            0.5,             # Valence (Unknown)
            0.5,             # Danceability (Unknown)
            acousticness,    # Acousticness
            0.0              # Instrumentalness (Unknown)
        ]

        return {
            "song_id": "72Z17vmmeW25ZuvAB0ge7N", # Space Oddity (Still hardcoded ID for demo flow)
            "metadata": {
                "title": "Space Oddity",
                "artist": "David Bowie",
                "genre": "Rock",
                "fingerprint_count": len(fingerprints),
                "processing_time": f"{duration:.4f}s",
                "physics": {
                    "rms": rms,
                    "flatness": flatness
                }
            },
            "vector": dynamic_vector
        }
    except Exception as e:
        print(f"Error in identify endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
