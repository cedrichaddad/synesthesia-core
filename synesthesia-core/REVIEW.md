# Code Review: Synesthesia Core
**Reviewer**: Senior Engineer Supervisor
**Date**: 2025-11-21
**Status**: ⚠️ NEEDS IMPROVEMENT

I've taken a deep dive into the codebase. There's some solid engineering here—the hybrid Rust/Python architecture is the right choice for this problem space, and the frontend aesthetic is coming together.

However, I found several **critical issues** that will prevent this from scaling or even working reliably in production. We need to address these before we ship.

---

## 🚨 Critical Issues (Must Fix)

### 1. The N+1 Problem in Spotify Client (Performance)
**File**: `python/synesthesia/spotify.py`

In `get_initial_tracks`, you are fetching a list of tracks and then iterating over them. Inside the loop, you call `_format_track`, which calls `self.sp.artist(artist_id)`.

```python
# python/synesthesia/spotify.py
for item in results['items']:
    tracks.append(self._format_track(item)) # <--- CALLS API INSIDE LOOP
```

**The Problem**: If you fetch 50 tracks, you are making **51 API calls** (1 for the list + 50 for artists). This will hit rate limits immediately and make the endpoint incredibly slow (~10-20 seconds latency).

**The Fix**:
Fetch all artist IDs in a single batch call using `sp.artists(ids=[...])` *before* the loop, create a lookup map, and then format the tracks.

### 2. Memory Allocation in Audio Loop (Rust Performance)
**File**: `src/audio.rs`

You are recalculating the Hanning window *every single time* `fingerprint` is called.

```rust
// src/audio.rs
let window = hanning_window(WINDOW_SIZE); // In prod, cache this!
```

**The Problem**: You allocated memory and computed 4096 floats for every chunk of audio. In a real-time context, this causes unnecessary GC pressure (or allocator pressure in Rust) and CPU cycles.

**The Fix**:
Move `window` into the `AudioFingerprinter` struct and initialize it once in `new()`.

### 3. DoS Vulnerability in File Upload
**File**: `python/synesthesia/api.py`

```python
# python/synesthesia/api.py
contents = await file.read() # <--- DANGEROUS
```

**The Problem**: This reads the entire uploaded file into RAM. If a user uploads a 100MB WAV file (or a malicious 10GB file), your server runs out of memory and crashes.

**The Fix**:
Use `spooled_temp_file` or stream the upload in chunks to a temporary file on disk, then process it.

---

## ⚠️ Architectural & Logic Concerns

### 4. "Zero-Shot" Vector Generation Flaw
**File**: `python/synesthesia/api.py`

When a song isn't in Qdrant, you generate a vector using `get_concept_vector(prompt)`.
**The Problem**: You are using the **Text Encoder** of the CLAP model to approximate the **Audio Embedding** of a song based on its metadata description. While clever, this is semantically different. A text description of "A funk song by Daft Punk" does not necessarily map to the same vector space location as the actual audio of "Get Lucky". This will degrade recommendation quality for new tracks.

### 5. Frontend Re-renders
**File**: `frontend/components/ui/Knob.tsx`

```typescript
useEffect(() => {
    // ...
}, [isDragging, onChange]); // <--- onChange changes every render?
```

**The Problem**: If the parent component doesn't wrap `onChange` in `useCallback`, this effect tears down and re-adds event listeners on every single frame of the drag, which is wasteful.

---

## 🛠️ Code Quality & Nitpicks

-   **Rust/Python Bridge**: You are passing `Vec<f32>` to Rust. This copies the data. Use `numpy::PyReadonlyArray1<f32>` to pass a view of the numpy array directly to Rust (Zero-Copy).
-   **Hardcoded Sample Rates**: `BAND_SPLITS` in `audio.rs` assumes 44.1kHz. If we process 48kHz audio, the frequency bands will be shifted.
-   **Mocking in Production Code**: `identify` endpoint returns hardcoded mock data. This needs to be flagged with a `TODO` or removed before any real deployment.

---

## 📋 Action Plan

1.  **Refactor `SpotifyClient`** to batch artist lookups.
2.  **Optimize `AudioFingerprinter`** in Rust to cache the window.
3.  **Secure `identify` endpoint** to handle file streams properly.
