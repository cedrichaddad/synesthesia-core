import sys
from qdrant_client import QdrantClient
from qdrant_client.http import models

def clean_invalid_points():
    print("🧹 Starting Cleanup of Invalid Points...")
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        collection_name = "synesthesia_tracks"
        
        # Scroll through all points
        offset = None
        invalid_ids = []
        
        while True:
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                with_payload=True,
                offset=offset
            )
            
            for point in points:
                if not point.payload or 'spotify_id' not in point.payload:
                    print(f"❌ Found invalid point: {point.id}")
                    invalid_ids.append(point.id)
            
            if next_offset is None:
                break
            offset = next_offset
            
        if invalid_ids:
            print(f"⚠️  Found {len(invalid_ids)} invalid points. Deleting...")
            client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=invalid_ids
                )
            )
            print("✅ Cleanup Complete.")
        else:
            print("✅ No invalid points found.")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clean_invalid_points()
