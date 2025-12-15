import whisper
import tempfile
import os
from typing import List
from app.ingestion.processors.base import BaseProcessor
from app.ingestion.models import Document, IngestionMetadata
import torch

class AudioVideoProcessor(BaseProcessor):
    def __init__(self):
        # Load model only once or on demand. 
        # For production, might want 'base' or 'small' to start, or configurable.
        # Using 'tiny' for speed in development/demo.
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model("tiny", device=device)
        
        import shutil
        if not shutil.which("ffmpeg"):
            print("WARNING: 'ffmpeg' not found in PATH. Audio/Video ingestion will fail.")

    def process(self, file_content: bytes, filename: str, mime_type: str) -> List[Document]:
        import shutil
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg is not installed or not in PATH. Please install FFmpeg to process audio/video files.")

        # Whisper requires a file path, so write to temp file
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        try:
            result = self.model.transcribe(tmp_path)
            segments = result.get("segments", [])
            
            documents = []
            for segment in segments:
                documents.append(Document(
                    content=segment["text"],
                    metadata=IngestionMetadata(
                        source_filename=filename,
                        file_type=mime_type,
                        timestamp_start=segment["start"],
                        timestamp_end=segment["end"],
                        extraction_method="whisper_stt"
                    )
                ))
            return documents
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
