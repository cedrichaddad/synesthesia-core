import os
import random
import sys
from qdrant_client import QdrantClient
from synesthesia.spotify import SpotifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_integrity():
    print("🔍 Starting System Integrity Verification...")
    
    # 1. Initialize Clients
    try:
        qdrant = QdrantClient(host="localhost", port=6333)
        spotify = SpotifyClient()
        print("✅ Clients initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        sys.exit(1)

    collection_name = "synesthesia_tracks"

    # 2. Get Total Count
    try:
        count_result = qdrant.count(collection_name=collection_name)
        total_points = count_result.count
        print(f"📊 Total points in Qdrant: {total_points}")
        
        if total_points == 0:
            print("⚠️  Database is empty! Run ingestion script.")
            sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to get count from Qdrant: {e}")
        sys.exit(1)

    # 3. Randomly Sample 5 Points
    print("\n🎲 Sampling 5 random points for verification...")
    
    # Qdrant doesn't support random sampling directly efficiently for large datasets without scrolling,
    # but for verification we can scroll a bit or use random offsets if we knew IDs.
    # A simple approach for a health check is to scroll with a random offset if supported, 
    # or just fetch the first 100 and pick 5 random ones (assuming uniform distribution isn't critical for a simple check).
    # Better: Scroll to a random offset.
    
    # Since we can't easily jump to a random offset without iterating, let's just grab a batch 
    # and verify them. If we want true random, we'd need all IDs.
    # Let's just grab the first batch for now to ensure *some* data is valid.
    
    points, _ = qdrant.scroll(
        collection_name=collection_name,
        limit=20,
        with_payload=True
    )
    
    if not points:
        print("❌ No points returned from scroll.")
        sys.exit(1)
        
    sample_points = random.sample(points, min(5, len(points)))
    
    success_count = 0
    
    for point in sample_points:
        qdrant_id = point.id
        payload = point.payload
        
        if not payload or 'spotify_id' not in payload:
            print(f"❌ Point {qdrant_id}: Missing 'spotify_id' in payload.")
            continue
            
        spotify_id = payload['spotify_id']
        title = payload.get('title', 'Unknown Title')
        
        print(f"   Checking: {title} (ID: {spotify_id})...", end=" ")
        
        try:
            # Verify against Spotify API
            track = spotify.sp.track(spotify_id)
            if track and track['id'] == spotify_id:
                print("✅ OK")
                success_count += 1
            else:
                print("❌ Mismatch or Not Found")
        except Exception as e:
            print(f"❌ Spotify API Error: {e}")

    print(f"\n🏁 Verification Complete: {success_count}/{len(sample_points)} checks passed.")
    
    if success_count == len(sample_points):
        print("✅ SYSTEM INTEGRITY: HEALTHY")
        sys.exit(0)
    else:
        print("❌ SYSTEM INTEGRITY: COMPROMISED")
        sys.exit(1)

if __name__ == "__main__":
    verify_integrity()
