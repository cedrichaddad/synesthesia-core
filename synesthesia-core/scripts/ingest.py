import time

# ... (imports)

    points = []
    for track in tracks:
        try:
            # Rate Limiting
            time.sleep(0.5)
            
            # Generate prompt
            prompt = f"A {track['genre']} track by {track['artist']} titled {track['title']}"
            print(f"Processing: {prompt}")
            
            # Generate vector
            vector = vector_engine.get_concept_vector(prompt)
            
            # Generate deterministic ID
            song_id = hashlib.sha256(prompt.encode()).hexdigest()[:12]
            
            # Create Qdrant point
            point = models.PointStruct(
                id=song_id,
                vector=vector.tolist(),
                payload={
                    "artist": track['artist'],
                    "title": track['title'],
                    "genre": track['genre'],
                    "prompt": prompt
                }
            )
            points.append(point)
        except Exception as e:
            print(f"Skipping track {track.get('title', 'Unknown')}: {e}")
            continue

    # Upsert to Qdrant
    if points:
        print(f"Upserting {len(points)} points to Qdrant...")
        try:
            vector_engine.qdrant.upsert(
                collection_name=vector_engine.collection_name,
                points=points
            )
            print("Ingestion complete!")
        except Exception as e:
            print(f"Error upserting to Qdrant: {e}")
    else:
        print("No tracks to ingest.")

if __name__ == "__main__":
    ingest_playlist()
