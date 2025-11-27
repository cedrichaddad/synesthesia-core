import requests
import time

BASE_URL = "http://localhost:8000"

def test_identify():
    print("Testing /identify...")
    with open("test_audio.wav", "rb") as f:
        files = {"file": ("test_audio.wav", f, "audio/wav")}
        response = requests.post(f"{BASE_URL}/identify", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ /identify Success")
        print(f"  Song: {data['metadata']['title']}")
        print(f"  Processing Time: {data['metadata']['processing_time']}")
        if 'physics' in data['metadata']:
            print(f"  RMS: {data['metadata']['physics']['rms']}")
            print(f"  Flatness: {data['metadata']['physics']['flatness']}")
        else:
            print("❌ Physics metadata missing!")
        return data['song_id']
    else:
        print(f"❌ /identify Failed: {response.text}")
        return None

def test_recommend(current_song_id):
    print("\nTesting /recommend...")
    payload = {
        "current_song_id": current_song_id,
        "knobs": {
            "Energy": 0.5,
            "Drums": 0.2
        }
    }
    response = requests.post(f"{BASE_URL}/recommend", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ /recommend Success")
        print(f"  Vector: {data['vector']}")
        print(f"  Recommendations: {len(data['songs'])}")
        for song in data['songs']:
            print(f"    - {song['title']} ({song['source'] if 'source' in song else 'Unknown Source'})")
    else:
        print(f"❌ /recommend Failed: {response.text}")

def test_ingest():
    print("\nTesting /ingest_playlist...")
    response = requests.post(f"{BASE_URL}/ingest_playlist")
    if response.status_code == 200:
        print(f"✅ /ingest_playlist Success: {response.json()}")
        # Wait for background task to finish (mock wait)
        print("  Waiting for background ingestion...")
        time.sleep(5) 
    else:
        print(f"❌ /ingest_playlist Failed: {response.text}")

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(2)
    
    test_ingest()
    
    song_id = test_identify()
    if song_id:
        # We need a valid UUID for recommend if we are strictly checking DB
        # But for now let's try with the ID returned (which is Space Oddity ID)
        # Note: Space Oddity might not be in our DB yet unless we ingested it.
        # But let's try.
        test_recommend(song_id)

    # Test Robustness: Recommend an unknown song (Bohemian Rhapsody)
    # Spotify ID: 1AhDOtG9vPSOmsWgNW0BEY
    print("\nTesting /recommend with UNKNOWN song (Bohemian Rhapsody)...")
    test_recommend("1AhDOtG9vPSOmsWgNW0BEY")
