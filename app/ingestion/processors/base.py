from abc import ABC, abstractmethod
from typing import List, BinaryIO
from app.ingestion.models import Document

class BaseProcessor(ABC):
    @abstractmethod
    def process(self, file_content: bytes, filename: str, mime_type: str) -> List[Document]:
        """
        Process the raw file content and return a list of Documents with metadata.
        """
        pass
