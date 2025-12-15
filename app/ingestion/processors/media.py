import fitz  # PyMuPDF
# import pytesseract (Moved to lazy import)
from PIL import Image
import io
from typing import List
from app.ingestion.processors.base import BaseProcessor
from app.ingestion.models import Document, IngestionMetadata

class MediaProcessor(BaseProcessor):
    def process(self, file_content: bytes, filename: str, mime_type: str) -> List[Document]:
        if mime_type == "application/pdf":
            return self._process_pdf(file_content, filename)
        elif mime_type.startswith("image/"):
            return self._process_image(file_content, filename, mime_type)
        else:
            raise ValueError(f"Unsupported media type for MediaProcessor: {mime_type}")

    def _process_pdf(self, file_content: bytes, filename: str) -> List[Document]:
        documents = []
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # If very little text is found, try OCR on the page image
                extraction_method = "text_extraction"
                if not text.strip():
                     # Render page to image
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # Try EasyOCR (Pure Python, no binary dependency)
                    try:
                        import easyocr
                        import numpy as np
                        
                        # Lazy load reader (WARNING: Heavy model load)
                        if not hasattr(self, 'ocr_reader'):
                             #gpu=False helps compatibility on simple setups
                             self.ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                        
                        # EasyOCR expects numpy array or bytes
                        # pix.tobytes gives bytes.
                        result = self.ocr_reader.readtext(img_data, detail=0)
                        text = " ".join(result)
                        extraction_method = "easyocr"
                        
                        # Log OCR Output
                        from app.core.logging import get_ocr_logger
                        ocr_logger = get_ocr_logger()
                        ocr_logger.info(f"File: {filename} | Page: {page_num+1} | Method: EasyOCR\nText Content:\n{text}\n{'-'*50}")
                        
                    except ImportError:
                        print("EasyOCR not installed. Run `pip install easyocr`.")
                        text = ""
                    except Exception as e:
                        print(f"EasyOCR Error: {e}")
                        text = ""

                if text.strip():
                    documents.append(Document(
                        content=text,
                        metadata=IngestionMetadata(
                            source_filename=filename,
                            file_type="application/pdf",
                            page_number=page_num + 1,
                            extraction_method=extraction_method
                        )
                    ))
        return documents

    def _process_image(self, file_content: bytes, filename: str, mime_type: str) -> List[Document]:
        # Try EasyOCR
        try:
            import easyocr
            
            if not hasattr(self, 'ocr_reader'):
                 self.ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            
            result = self.ocr_reader.readtext(file_content, detail=0)
            text = " ".join(result)
            
            # Log OCR Output
            from app.core.logging import get_ocr_logger
            ocr_logger = get_ocr_logger()
            ocr_logger.info(f"File: {filename} | Type: {mime_type} | Method: EasyOCR\nText Content:\n{text}\n{'-'*50}")
            
        except ImportError:
             raise ValueError("EasyOCR not installed. Please install it for image processing.")
        except Exception as e:
             raise ValueError(f"EasyOCR processing failed: {e}")
        
        if not text.strip():
            return []

        return [Document(
            content=text,
            metadata=IngestionMetadata(
                source_filename=filename,
                file_type=mime_type,
                extraction_method="easyocr",
                page_number=1
            )
        )]
