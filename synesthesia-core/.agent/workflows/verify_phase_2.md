---
description: Verify Phase 2 (Physics Engine) implementation
---

This workflow verifies the backend API endpoints for Synesthesia v1.0 Phase 2.

1. **Ensure the API Server is Running**
   If you haven't started it yet, run:
   ```bash
   source .venv/bin/activate && python3 -m uvicorn python.synesthesia.api:app --reload --port 8000
   ```

2. **Generate Test Audio (if needed)**
   Create a dummy audio file for testing:
   ```bash
   ffmpeg -f lavfi -i "sine=frequency=1000:duration=1" -c:a pcm_s16le test_audio.wav -y
   ```

3. **Run the Verification Script**
   This script tests `/ingest_playlist`, `/identify`, and `/recommend`.
   ```bash
   source .venv/bin/activate && python3 verify_phase2.py
   ```

**Expected Output:**
- `✅ /ingest_playlist Success`: Confirms tracks were fetched (Mock or Spotify) and sent to Qdrant.
- `✅ /identify Success`: Confirms audio was processed by Rust core (RMS/Flatness calculated).
- `✅ /recommend Success` (or Failure if DB empty): Confirms recommendation logic.

**Note:** If `/recommend` fails with "Song not found", it means the specific song identified (Space Oddity) wasn't in the random set of tracks ingested. This is expected behavior for the demo until we have a larger dataset.
