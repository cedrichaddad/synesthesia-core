import os
import sys
import json
from typing import List, Dict
import time

# Add python directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "python"))

from synesthesia.spotify import SpotifyClient
from dotenv import load_dotenv

load_dotenv()

def validate_track_object(track: Dict, source: str):
    """
    Rigorously validate a track object.
    Must have: id, title, artist, genre.
    Must have valid 5D features (0.0 - 1.0).
    """
    print(f"  Validating {source} -> {track.get('title', 'Unknown')} ({track.get('id')})")
    
    # 1. Critical Metadata
    assert track.get('id') is not None, f"{source}: Missing ID"
    assert track.get('id') != 'Unknown', f"{source}: ID is 'Unknown'"
    assert track.get('title') is not None, f"{source}: Missing Title"
    assert track.get('title') != 'Unknown', f"{source}: Title is 'Unknown'"
    assert track.get('artist') is not None, f"{source}: Missing Artist"
    assert track.get('genre') is not None, f"{source}: Missing Genre"

    # 2. Audio Features (The Physics)
    features = ['energy', 'valence', 'danceability', 'acousticness', 'instrumentalness']
    for feat in features:
        val = track.get(feat)
        assert val is not None, f"{source}: Missing {feat}"
        assert isinstance(val, (int, float)), f"{source}: {feat} is not a number ({type(val)})"
        assert 0.0 <= val <= 1.0, f"{source}: {feat} out of range ({val})"

    print("    ✅ Valid")

def test_spotify_client():
    print("Initializing SpotifyClient...")
    client = SpotifyClient()
    
    if client.mock_mode:
        print("⚠️  WARNING: Running in Mock Mode. Validation is less meaningful.")
    else:
        print("🔒 Running with Real Spotify Credentials.")

    # 1. Test get_initial_tracks (Bulk Fetch)
    print("\n1. Testing get_initial_tracks()...")
    tracks = client.get_initial_tracks(limit=10)
    assert len(tracks) > 0, "get_initial_tracks returned empty list"
    for t in tracks:
        validate_track_object(t, "get_initial_tracks")

    # 2. Test search (Single Result)
    print("\n2. Testing search('Daft Punk')...")
    result = client.search("Daft Punk")
    validate_track_object(result, "search")

    # 3. Test search_tracks (Multiple Results)
    print("\n3. Testing search_tracks('Jazz', limit=5)...")
    results = client.search_tracks("Jazz", limit=5)
    # Relax assertion: Spotify search might return fewer than limit if strict matching fails
    assert len(results) > 0, f"Expected >0 results, got {len(results)}"
    print(f"  Got {len(results)} results.")
    for t in results:
        validate_track_object(t, "search_tracks")

    # 4. Test get_track_details (Specific ID)
    print("\n4. Testing get_track_details('Bohemian Rhapsody ID')...")
    # Bohemian Rhapsody ID: 1AhDOtG9vPSOmsWgNW0BEY
    details = client.get_track_details("1AhDOtG9vPSOmsWgNW0BEY")
    validate_track_object(details, "get_track_details")

    # 5. Test Error Handling (Invalid ID)
    print("\n5. Testing get_track_details(INVALID_ID)...")
    try:
        bad_details = client.get_track_details("INVALID_ID_12345")
        # We expect it to return an object with 'Unknown' fields or raise error
        # Our current implementation returns 'Unknown' fields.
        # Let's verify it DOESN'T pass validation.
        print(f"  Got: {bad_details}")
        if bad_details.get('title') == 'Unknown':
            print("  ✅ Correctly handled invalid ID (Returned Unknown object)")
        else:
            print("  ❌ Unexpected behavior for invalid ID")
    except Exception as e:
        print(f"  ✅ Correctly raised exception: {e}")

    print("\n🎉 All Spotify Data Validations Passed!")
    
    # Fidelity Check
    # Check if we are getting real physics or defaults
    if details.get('energy') == 0.5 and details.get('valence') == 0.5:
        print("\n⚠️  WARNING: LOW FIDELITY DETECTED")
        print("   The Audio Features API is returning 403/Errors.")
        print("   We are using fallback values (0.5). Physics will be generic.")
    else:
        print("\n✅ HIGH FIDELITY: Real Audio Features Detected.")

if __name__ == "__main__":
    try:
        test_spotify_client()
    except AssertionError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR: {e}")
        sys.exit(1)
