import asyncio
import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())
from app.db.vector_store_client import QdrantVectorStore
from app.core.config import get_settings

settings = get_settings()

def inspect_db():
    print("--- Inspecting Vector DB ---")
    print(f"Location: {settings.QDRANT_LOCATION}")
    print(f"Host: {settings.QDRANT_HOST}")
    
    try:
        client = QdrantVectorStore()
        # Qdrant local client doesn't support all http methods, but let's try getting collection info
        # Access the inner QdrantClient
        q_client = client.client
        
        collections = q_client.get_collections()
        print(f"\nCollections: {[c.name for c in collections.collections]}")
        
        if collections.collections:
            name = collections.collections[0].name
            info = q_client.get_collection(name)
            print(f"\nCollection '{name}' Status: {info.status}")
            print(f"Vectors Count: {info.points_count}")
            
            if info.points_count > 0:
                print("\nSample Point Payload:")
                res, _ = q_client.scroll(
                    collection_name=name,
                    limit=1,
                    with_payload=True,
                    with_vectors=False
                )
                if res:
                    print(res[0].payload)
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    inspect_db()
