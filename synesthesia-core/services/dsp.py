import sounddevice as sd
import numpy as np
import threading
import queue
import time
import collections
from typing import Optional

# Try to import the Rust extension
try:
    from synesthesia.core import audio_analyze, audio_fingerprint
except ImportError:
    audio_analyze = None
    audio_fingerprint = None

class DSP:
    def __init__(self, sample_rate=44100, block_size=2048):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.queue = queue.Queue()
        self.running = False
        self.paused = False
        self.stream = None
        self.thread = None
        
        # Buffering for Fingerprinting (needs > 4096 samples)
        self.min_size = 4096 + 2048 # Window + Hop
        # Use deque for O(1) appends, maxlen prevents infinite growth
        self.buffer = collections.deque(maxlen=self.min_size * 2)

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def start(self):
        if self.running:
            return
            
        self.running = True
        
        # If Rust extension is missing or sounddevice fails, we might want a fallback
        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self.audio_callback
            )
            self.stream.start()
        except Exception:
            # Failed to start audio stream, starting Mock DSP thread
            self.thread = threading.Thread(target=self._mock_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
        self.stream = None

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            pass
        if not self.running or self.paused:
            return

        # indata is numpy array (frames, channels)
        # Flatten to 1D array for Rust
        audio_data = indata[:, 0].astype(np.float32)
        
        # Efficient append
        self.buffer.extend(audio_data)

        fingerprints = []
        
        # Process if we have enough data
        if len(self.buffer) >= self.min_size:
            # Convert deque to numpy array for Rust (copy is unavoidable here but better than np.append)
            # We take the last N samples needed
            chunk = np.array(self.buffer, dtype=np.float32)
            
            if audio_fingerprint:
                # Returns list of (hash, time_offset)
                raw_fingerprints = audio_fingerprint(chunk)
                
                # Unpack hashes for visualization
                # Rust pack_hash: ((f1 as u64) << 20) | ((f2 as u64) << 8) | (dt as u64)
                # Layout: [Unused: 32] [F1: 12] [F2: 12] [Delta: 8]
                for (h, t) in raw_fingerprints:
                    f1 = (h >> 20) & 0xFFF
                    dt = h & 0xFF
                    fingerprints.append((f1, dt))
            
            # Note: deque handles the sliding window automatically via maxlen, 
            # but for overlapping FFTs we just keep streaming.
        
        try:
            if audio_analyze:
                # Call Rust extension
                rms, flatness = audio_analyze(audio_data)
            else:
                # Fallback python calc
                rms = np.sqrt(np.mean(audio_data**2))
                flatness = 0.5 # Placeholder
            
            # Create AudioFeatures dict
            features = {
                "rms": float(rms),
                "spectral_centroid": float(flatness), # Using flatness as proxy
                "bpm": 120.0, # Mock
                "is_transient": rms > 0.1, # Simple threshold
                "stars": fingerprints
            }
            
            # Avoid queue overflow
            if self.queue.qsize() < 10:
                self.queue.put(features)
                
        except Exception:
            pass

    def _mock_loop(self):
        """Generates fake data if microphone is unavailable."""
        import random
        import math
        
        t = 0.0
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            t += 0.1
            rms = (math.sin(t) + 1) / 2 * 0.5
            flatness = random.random()
            
            # Mock stars
            stars = []
            if random.random() > 0.5:
                for _ in range(random.randint(1, 5)):
                    f1 = random.randint(100, 4000)
                    dt = random.randint(1, 60)
                    stars.append((f1, dt))

            features = {
                "rms": rms,
                "spectral_centroid": flatness,
                "bpm": 120.0,
                "is_transient": rms > 0.8,
                "stars": stars
            }
            
            if self.queue.qsize() < 10:
                self.queue.put(features)
            
            time.sleep(0.1)
