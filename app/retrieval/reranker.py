from sentence_transformers import CrossEncoder
from typing import List
from app.retrieval.models import SearchResult
import logging

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize CrossEncoder.
        This model is trained to predict relevance score of (query, document) pairs.
        """
        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, results: List[SearchResult], top_k: int = None) -> List[SearchResult]:
        if not results:
            return []

        # Prepare pairs [query, content]
        pairs = [[query, res.content] for res in results]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Update scores and sort
        for i, res in enumerate(results):
            res.score = float(scores[i])
            
        # Sort descending by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        if top_k:
            return results[:top_k]
        
        return results
