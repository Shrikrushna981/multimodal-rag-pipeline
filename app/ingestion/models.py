from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class IngestionMetadata(BaseModel):
    source_filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type or extension")
    page_number: Optional[int] = Field(None, description="Page number for documents")
    timestamp_start: Optional[float] = Field(None, description="Start time in seconds for AV")
    timestamp_end: Optional[float] = Field(None, description="End time in seconds for AV")
    extraction_method: str = Field(..., description="Method used: text, ocr, whisper_stt")
    category: str = Field(default="Uncategorized", description="Document category")
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

class Document(BaseModel):
    content: str
    metadata: IngestionMetadata

class IngestionResponse(BaseModel):
    task_id: str
    status: IngestionStatus
    message: str = "Ingestion started"
