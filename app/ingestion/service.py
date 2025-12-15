import filetype
import logging
import uuid
from typing import Dict, List
from app.ingestion.processors.base import BaseProcessor
from app.ingestion.processors.media import MediaProcessor
from app.ingestion.processors.av import AudioVideoProcessor
from app.ingestion.models import IngestionResponse, IngestionStatus
from app.ingestion.chunker import Chunker
from app.llm.embedding_service import EmbeddingService
from app.db.vector_store_client import QdrantVectorStore

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self):
        # Processors
        self.media_processor = MediaProcessor()
        self.av_processor = AudioVideoProcessor()
        
        # Pipeline Components
        self.chunker = Chunker()
        self.embedding_service = EmbeddingService(provider="local")
        
        # Vector DB - In production config, host/port should come from settings
        # Using memory for dev/demo if needed, or localhost default
        self.vector_store = QdrantVectorStore() 
        self.collection_name = "rag_collection"
        
        # Ensure collection exists
        try:
            self.vector_store.create_collection(
                self.collection_name, 
                self.embedding_service.dimension
            )
        except Exception as e:
            logger.warning(f"Could not create collection (might exist or DB down): {e}")

    async def process_file(self, file_content: bytes, filename: str, category: str = "Uncategorized") -> str:
        task_id = str(uuid.uuid4())
        return task_id

    async def process_background(self, task_id: str, file_content: bytes, filename: str, category: str = "Uncategorized"):
        logger.info(f"Task {task_id}: Starting ingestion for {filename} (Category: {category})")
        
        try:
            kind = filetype.guess(file_content)
            mime_type = kind.mime if kind else "application/octet-stream"
            
            processor: BaseProcessor = None
            
            if mime_type == "application/pdf" or mime_type.startswith("image/"):
                processor = self.media_processor
            elif mime_type.startswith("audio/") or mime_type.startswith("video/"):
                processor = self.av_processor
            
            if not processor:
                logger.warning(f"Task {task_id}: Unsupported file type {mime_type}")
                return

            # 1. Extraction
            documents = processor.process(file_content, filename, mime_type)
            
            # Apply Category
            for doc in documents:
                doc.metadata.category = category
                
            logger.info(f"Task {task_id}: Extracted {len(documents)} raw documents/segments.")
            
            # 2. Chunking
            chunked_docs = self.chunker.chunk_documents(documents)
            logger.info(f"Task {task_id}: Created {len(chunked_docs)} chunks.")
            
            if not chunked_docs:
                logger.info(f"Task {task_id}: No content to index.")
                return

            # 3. Embedding
            texts = [doc.content for doc in chunked_docs]
            embeddings = self.embedding_service.embed_documents(texts)
            
            # 4. Storage (Vector DB)
            points = []
            for i, doc in enumerate(chunked_docs):
                payload = doc.metadata.model_dump(mode='json')
                payload["content"] = doc.content # Store text in payload for retrieval
                
                points.append({
                    "vector": embeddings[i],
                    "payload": payload
                })
            
            self.vector_store.upsert(self.collection_name, points)
            
            logger.info(f"Task {task_id}: Successfully indexed {len(points)} vectors.")

        except Exception as e:
            logger.error(f"Task {task_id}: Ingestion failed - {str(e)}", exc_info=True)
