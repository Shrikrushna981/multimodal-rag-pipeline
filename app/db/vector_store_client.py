from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import uuid
import hashlib
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from app.core.config import get_settings

settings = get_settings()

class VectorStoreClient(ABC):
    @abstractmethod
    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        """
        Upsert vectors with metadata.
        points structure: [{"id": str, "vector": list, "payload": dict}]
        """
        pass

    @abstractmethod
    def search(self, collection_name: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, vector_size: int) -> None:
        pass

class QdrantVectorStore(VectorStoreClient):
    _client_instance = None
    
    def __init__(self):
        if QdrantVectorStore._client_instance:
             self.client = QdrantVectorStore._client_instance
        else:
             if settings.QDRANT_LOCATION:
                 # Check if it looks like a path (starts with . or / or C:) or is :memory:
                 # If it is a URL (starts with http), use url=
                 if settings.QDRANT_LOCATION.startswith("http"):
                     self.client = QdrantClient(url=settings.QDRANT_LOCATION)
                 else:
                     self.client = QdrantClient(path=settings.QDRANT_LOCATION)
             else:
                 self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
             
             # Save singleton
             QdrantVectorStore._client_instance = self.client

    def create_collection(self, collection_name: str, vector_size: int):
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=rest.VectorParams(
                    size=vector_size,
                    distance=rest.Distance.COSINE
                )
            )
            # Create payload index for filtering
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="source_filename",
                field_schema=rest.PayloadSchemaType.KEYWORD
            )

    def upsert(self, collection_name: str, points: List[Dict[str, Any]]):
        # Convert dict points to PointStructs
        points_structs = [
            rest.PointStruct(
                id=p.get("id", self._generate_id(p.get("payload", {}).get("content", str(uuid.uuid4())))),
                vector=p["vector"],
                payload=p.get("payload", {})
            )
            for p in points
        ]
        self.client.upsert(
            collection_name=collection_name,
            points=points_structs
        )

    def search(self, collection_name: str, query_vector: List[float], limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query_filter = None
        if filters:
            # Simple exact match filter construction
            must_conditions = []
            for key, value in filters.items():
                if isinstance(value, list) and value:
                    must_conditions.append(
                        rest.FieldCondition(
                            key=key, 
                            match=rest.MatchAny(any=value)
                        )
                    )
                elif value is not None:
                    must_conditions.append(
                        rest.FieldCondition(
                            key=key, 
                            match=rest.MatchValue(value=value)
                        )
                    )
            if must_conditions:
                 query_filter = rest.Filter(must=must_conditions)

        # DEBUG: Check client
        # if not hasattr(self.client, "search"): ... (Removed debug)

        # Use query_points for newer clients that lack .search()
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        ).points
        
        return [
            {"id": hit.id, "score": hit.score, "payload": hit.payload}
            for hit in results
        ]

    def _generate_id(self, content: str) -> str:
        """Generate a deterministic UUID based on content hash for idempotency."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, hashlib.md5(content.encode()).hexdigest()))
