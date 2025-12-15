from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.ingestion.models import Document, IngestionMetadata

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_document(self, document: Document) -> List[Document]:
        """
        Splits a single document into multiple chunked documents.
        Preserves and updates metadata.
        """
        # If content is empty or not text (e.g. pure image without OCR), return as is or handle accordingly
        if not document.content:
            return [document]

        chunks = self.text_splitter.split_text(document.content)
        chunked_docs = []
        
        for i, chunk in enumerate(chunks):
            # Create a copy of metadata
            new_metadata = document.metadata.model_copy()
            # We could add chunk_index or ID here if needed
            
            chunked_docs.append(Document(
                content=chunk,
                metadata=new_metadata
            ))
            
        return chunked_docs

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
