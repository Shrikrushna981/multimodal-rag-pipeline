# 🚀 Run Prerequisites & Setup Guide

This document outlines the dependencies and configuration required to run the Multimodal RAG application locally.

## 1. System Dependencies
These tools must be installed on your OS for ingestion to work.

### Windows (Method 1: Winget/Choco)
- **Tesseract OCR** (For Images/PDFs):  
  Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).  
  *Important*: Add the installation path (e.g., `C:\Program Files\Tesseract-OCR`) to your System PATH variables.
- **FFmpeg** (For Audio/Video):  
  `winget install Gyan.FFmpeg`  
  Or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add `bin` folder to PATH.

### Verify Installation
Open a new terminal and run:
```bash
tesseract --version
ffmpeg -version
```

## 2. Infrastructure (Docker)
The application requires a Vector Database (Qdrant). The easiest way to run this is via Docker.

### Run Qdrant
```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v qdrant_storage:/qdrant/storage \
    qdrant/qdrant:latest
```
*Note: If you don't have Docker, you can use Qdrant Cloud (Cloud API) and update `QDRANT_HOST` in `.env`.*

## 3. Environment Configuration
Create a `.env` file in the root directory (`d:\Documents\Projects\Multimodal-RAG Pipeline\.env`).

```ini
# Core
APP_NAME="Multimodal RAG"
DEBUG=True
LOG_LEVEL=INFO

# LLM Providers
# Required for Chat & Transcription
OPENAI_API_KEY=sk-proj-... 

# Vector DB
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=multimodal_rag

# Optional: LangSmith / LangChain Tracing
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=...
```

## 4. Python Environment
Install the python dependencies.

```bash
pip install -r requirements.txt
```

## 5. Running the Application

### Backend (FastAPI)
Start the API server on port 8000.
```bash
uvicorn app.main:app --reload --port 8000
```
*Check connectivity: http://localhost:8000/health*

### Frontend (Streamlit)
Start the UI on port 8501.
```bash
streamlit run ui/app.py
```

## 6. Running with Docker Compose (Recommended)
The easiest way to run the entire stack (Qdrant + Backend + UI) is with Docker Compose.

1. Ensure you have Docker Installed.
2. Create/Update your `.env` file with your `OPENAI_API_KEY`.
3. Run:
   ```bash
   docker-compose up --build
   ```
4. Access the UI at `http://localhost:8501`.

## 7. Usage Checklist
1. Open Streamlit UI (`http://localhost:8501`).
2. Go to sidebar, upload a PDF or Image.
3. Wait for "Ingestion Complete" (Check Backend logs for activity).
4. Start a chat asking about the document.
