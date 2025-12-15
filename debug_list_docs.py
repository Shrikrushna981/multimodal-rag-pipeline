from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import hashlib

def debug_docs():
    print("Connecting to Qdrant (Local ./qdrant_data)...")
    client = QdrantClient(path="./qdrant_data")
    
    collection_name = "rag_collection"
    if not client.collection_exists(collection_name):
        print(f"Collection {collection_name} does not exist!")
        return

    print(f"Collection {collection_name} exists.")
    
    # 1. Count
    count = client.count(collection_name).count
    print(f"Total points count: {count}")
    
    if count == 0:
        print("Collection is empty. Ingestion failed to persist or empty?")
        return

    # 2. Scroll to check payload
    res, _ = client.scroll(
        collection_name=collection_name,
        limit=5,
        with_payload=True
    )
    
    print("\nSAMPLE POINTS:")
    for point in res:
        print(f"ID: {point.id}")
        payload = point.payload or {}
        print(f"  Source: {payload.get('source_filename', 'N/A')}")
        print(f"  Keys: {list(payload.keys())}")
        print("-" * 20)

    # 3. Simulate aggregation
    res_all, _ = client.scroll(
        collection_name=collection_name,
        limit=1000,
        with_payload=True
    )
    docs = set()
    for point in res_all:
        p = point.payload or {}
        docs.add(p.get("source_filename", "UNKNOWN"))
    
    print(f"\nUnique filenames found via scroll(1000): {docs}")

if __name__ == "__main__":
    debug_docs()
