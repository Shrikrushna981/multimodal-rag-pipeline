from qdrant_client import QdrantClient
import os

try:
    print(f"Qdrant Client Version check...")
    import qdrant_client
    print(f"Version: {qdrant_client.__version__}")
    
    # Test Local Client
    client = QdrantClient(path="./qdrant_data_test")
    print("Client created.")
    print(f"Has 'search'? {'search' in dir(client)}")
    print(f"Has 'upsert'? {'upsert' in dir(client)}")
    
    if hasattr(client, 'search'):
        print("Search method exists.")
    else:
        print("Search method MISSING.")
        print("Available attributes:", dir(client))

except Exception as e:
    print(f"Error: {e}")
