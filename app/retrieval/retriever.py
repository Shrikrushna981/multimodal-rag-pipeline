from typing import List, Optional, Dict, Any
from app.llm.embedding_service import EmbeddingService
from app.db.vector_store_client import VectorStoreClient, QdrantVectorStore
from app.retrieval.models import RetrievalQuery, SearchResult, RetrievalResponse
from app.retrieval.reranker import Reranker
import logging

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self.embedding_service = EmbeddingService(provider="local")
        # In production, inject this or get from singletons
        self.vector_store = QdrantVectorStore() 
        self.collection_name = "rag_collection"
        
        # Optional Reranker
        # Lazy load to save memory if not needed or make optional
        self.reranker = Reranker()

    def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        """
        Executes the retrieval pipeline:
        1. Embed Query
        2. Vector Search (Top-K * candidate_factor)
        3. Rerank
        4. Return Top-K
        """
        # 1. Embed
        query_vector = self.embedding_service.embed_documents([query.query])[0]
        
        # Fetch more candidates for reranking (e.g. 3x)
        candidate_k = query.top_k * 3
        
        # 2. Search
        # Filters keys need to match payload fields. 
        # In ingestion/service.py: payload = doc.metadata.model_dump().
        # e.g. source_filename, file_type, page_number
        raw_results = self.vector_store.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=candidate_k,
            filters=query.filters
        )
        
        # Map to SearchResult
        results = []
        for hit in raw_results:
            payload = hit.get("payload", {})
            content = payload.get("content", "")
            # Exclude content from metadata to avoid duplication
            metadata = {k: v for k, v in payload.items() if k != "content"}
            
            results.append(SearchResult(
                id=hit["id"],
                score=hit["score"],
                content=content,
                metadata=metadata
            ))

        logger.info(f"Retrieved {len(results)} candidates for query: '{query.query}'")
        
        # 3. Rerank
        if query.use_reranker and self.reranker:
            final_results = self.reranker.rerank(query.query, results, top_k=query.top_k)
        else:
            final_results = results[:query.top_k]
        
        return RetrievalResponse(
            results=final_results,
            total_found=len(results)
        )
