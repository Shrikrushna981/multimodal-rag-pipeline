from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RetrievalQuery(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None # Simple key-value exact match for now
    include_metadata: bool = True
    use_reranker: bool = True

class SearchResult(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]
    id: str

class RetrievalResponse(BaseModel):
    results: List[SearchResult]
    total_found: int
