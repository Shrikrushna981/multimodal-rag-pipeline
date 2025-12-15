from abc import ABC, abstractmethod
from typing import List, Union
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingModel(ABC):
    @abstractmethod
    def embed_text(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

class LocalEmbeddingModel(EmbeddingModel):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
    
    def embed_text(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

class EmbeddingService:
    def __init__(self, provider: str = "local"):
        # Factory logic for providers
        if provider == "local":
            self.model = LocalEmbeddingModel()
        else:
            raise NotImplementedError(f"Provider {provider} not implemented")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.embed_text(texts)
    
    @property
    def dimension(self) -> int:
        return self.model.dimension
