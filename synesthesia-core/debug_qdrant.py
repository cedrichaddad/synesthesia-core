from qdrant_client import QdrantClient
import numpy as np

client = QdrantClient(path="./qdrant_storage")

collections = client.get_collections().collections
print(f"Found {len(collections)} collections.")

for col in collections:
    print(f"\n--- Collection: {col.name} ---")
    info = client.get_collection(col.name)
    print(f"Status: {info.status}")
    print(f"Points: {info.points_count}")
    print(f"Vectors Config: {info.config.params.vectors}")
    
    # Try a dummy search
    try:
        # Assuming 5D
        vector = [0.5, 0.5, 0.5, 0.5, 0.0]
        print(f"Attempting 5D search on {col.name}...")
        results = client.search(
            collection_name=col.name,
            query_vector=vector,
            limit=1
        )
        print(f"Result count: {len(results)}")
        if results:
            print(f"Top result: {results[0].payload.get('title', 'No Title')}")
    except Exception as e:
        print(f"Search failed: {e}")
