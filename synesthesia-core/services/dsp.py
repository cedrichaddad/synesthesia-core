import sounddevice as sd
import numpy as np
import threading
import queue
import time
from typing import Optional

# Try to import the Rust extension
try:
    from synesthesia.core import audio_analyze
except ImportError:
    audio_analyze = None

class DSP:
    def __init__(self, sample_rate=44100, block_size=2048):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.queue = queue.Queue()
        self.running = False
        self.paused = False
        self.stream = None
        self.thread = None

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
                "is_transient": rms > 0.1 # Simple threshold
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
            
            features = {
                "rms": rms,
                "spectral_centroid": flatness,
                "bpm": 120.0,
                "is_transient": rms > 0.8
            }
            
            if self.queue.qsize() < 10:
                self.queue.put(features)
            
            time.sleep(0.1)
