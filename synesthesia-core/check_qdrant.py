from services.vector import VectorEngine
import sys

try:
    ve = VectorEngine()
    count = ve.get_count()
    print(f"Collection Count: {count}")
    
    if count > 0:
        # Try a test search
        import numpy as np
        test_vector = np.array([0.5, 0.5, 0.5, 0.5, 0.0], dtype=np.float32)
        results = ve.search(test_vector, k=1)
        print(f"Test Search Result: {results}")
    else:
        print("Collection is empty!")

except Exception as e:
    print(f"Error: {e}")
