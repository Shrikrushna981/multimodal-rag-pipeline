# System Architecture

## High-Level Overview

The Multimodal RAG application is built as a modular microservices-ready architecture containing three main distinct parts:

1.  **Frontend (Streamlit)**: A user-friendly interface for uploading documents and chatting.
2.  **Backend (FastAPI)**: The core logic handling multimodal processing, vector storage, and LLM orchestration.
3.  **Vector Database (Qdrant)**: Stores embeddings and metadata for fast retrieval.

```mermaid
graph TD
    User[User] -->|Interacts| UI[Streamlit UI (Port 8501)]
    UI -->|HTTP Requests| API[FastAPI Backend (Port 8000)]
    
    subgraph Backend Services
        API -->|Async Task| Ingest[Ingestion Service]
        API -->|Request| Chat[Conversation Service]
        
        Ingest -->|OCR/Extract| Processor[Media/AV Processors]
        Processor -->|Text| Chunker[Chunker]
        Chunker -->|Text Segments| Embed[Embedding Model]
        Embed -->|Vectors| VectorDB[(Qdrant)]
        
        Chat -->|Query| Embed
        Chat -->|Search| VectorDB
        VectorDB -->|Results| Reranker[Cross-Encoder]
        Reranker -->|Top-K| Prompt[Prompt Builder]
        Prompt -->|Context| LLM[LLM Gateway (OpenAI)]
    end
    
    Ingest -->|Files| Storage[Temp Storage]
```

## Detailed Data Flow

### 1. Ingestion Pipeline
1.  **Upload**: User sends a file (PDF, Image, Audio, Video) via the `/ingest` endpoint.
2.  **Processing**:
    *   **PDF/Images**: Processed by `MediaProcessor` using `pytesseract` (OCR) and `pymupdf`.
    *   **Audio/Video**: Processed by `AudioVideoProcessor` using `openai-whisper` for transcription.
3.  **Chunking**: Text is split into overlapping chunks (e.g., 500 chars) to maintain context.
4.  **Embedding**: Chunks are converted to dense vectors using a local model (`all-MiniLM-L6-v2`).
5.  **Storage**: Vectors and functional metadata (filename, page number, timestamp) are stored in **Qdrant**.

### 2. Retrieval & Generation (RAG)
1.  **Query**: User sends a chat message.
2.  **Retrieval**:
    *   Query is embedded.
    *   **Vector Search**: Finds top candidates (e.g., top 15) from Qdrant.
    *   **Reranking**: A Cross-Encoder model re-scores the candidates for semantic relevance to select the best `Top-K` (e.g., 3).
3.  **Generation**:
    *   `PromptBuilder` constructs a prompt with System Context + Retrieved Knowledge + Chat History.
    *   `LLMGateway` sends this to OpenAI (with retry logic).
4.  **Streaming**: The response is streamed token-by-token back to the UI.

---

# Docker Commands

To run the application locally using Docker, ensure you have **Docker Desktop** installed and running.

### 1. Prerequisite: Configuration
Ensure your `.env` file is configured for Docker networking:
```ini
OPENAI_API_KEY=sk-proj-...
# Docker internal networking
QDRANT_HOST=qdrant
QDRANT_PORT=6333
# QDRANT_LOCATION should be commented out for Docker
# QDRANT_LOCATION=./qdrant_data 
```

### 2. Build and Start
Run this command in the project root:

```bash
docker-compose up --build
```

*   This builds the `rag-backend` and `rag-ui` images.
*   It pulls the `qdrant` image.
*   It starts all three services in the correct order.

### 3. Access
*   **UI**: [http://localhost:8501](http://localhost:8501)
*   **API**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### 4. Stop
To stop the application:
```bash
docker-compose down
```

### Troubleshooting Docker
If you see connection errors:
1.  **Check Logs**: `docker-compose logs -f backend`
2.  **Verify Qdrant**: Ensure the `qdrant` container is healthy (`docker ps`).
3.  **Network**: The backend uses the hostname `qdrant` to talk to the database. If you run manually without compose, this link breaks. Always use `docker-compose`.
