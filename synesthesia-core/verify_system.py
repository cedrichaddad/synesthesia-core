import sys
import numpy as np
import os

# Add python directory to path
sys.path.append(os.path.join(os.getcwd(), "python"))

try:
    import synesthesia.core as rust_core
    from synesthesia.vector import VectorEngine
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def verify_rust_core():
    print("\n--- Verifying Rust Core ---")
    # Generate 5 seconds of silence/noise
    audio = np.random.rand(44100 * 5).astype(np.float32)
    try:
        fingerprints = rust_core.audio_fingerprint(audio.tolist())
        print(f"✅ Audio fingerprinting successful. Generated {len(fingerprints)} fingerprints.")
        if len(fingerprints) > 0:
            print(f"   Sample hash: {fingerprints[0].hash}, Offset: {fingerprints[0].offset}")
    except Exception as e:
        print(f"❌ Audio fingerprinting failed: {e}")

def verify_vector_engine():
    print("\n--- Verifying Vector Engine ---")
    try:
        engine = VectorEngine()
        
        # Test vector arithmetic
        # We need a real ID in Qdrant for get_vector to work without fallback warning
        # But fallback is fine for verification
        v_current = engine.get_vector("song_1")
        v_concept = engine.get_concept_vector("Drums")
        
        # V_target = V_current + 0.5 * V_concept
        v_target = v_current + 0.5 * v_concept
        norm = np.linalg.norm(v_target)
        v_target_norm = v_target / norm
        
        print(f"✅ Vector arithmetic successful.")
        print(f"   Target vector norm: {np.linalg.norm(v_target_norm):.4f}")
        
        # Test search
        results = engine.search(v_target_norm)
        print(f"✅ Search successful. Results: {results}")
    except Exception as e:
        print(f"❌ Vector Engine failed: {e}")

if __name__ == "__main__":
    verify_rust_core()
    verify_vector_engine()
