# Comprehensive Project Overview: Multimodal RAG Pipeline

## Table of Contents
1. [What This Project Is](#what-this-project-is)
2. [High-Level Architecture](#high-level-architecture)
3. [Detailed Workflows](#detailed-workflows)
4. [Core Concepts & Technologies](#core-concepts--technologies)
5. [Project Structure](#project-structure-deep-dive)
6. [Technology Stack](#technology-stack)
7. [Key Algorithms & Techniques](#key-algorithms--techniques)
8. [Interview Talking Points](#interview-talking-points)
9. [Running the System](#running-the-system)
10. [Common Interview Questions](#common-interview-questions--answers)

---

## What This Project Is

**Multimodal RAG** is a production-ready retrieval-augmented generation (RAG) pipeline that ingests multimodal content (PDFs, images, audio, and video), converts it into vector embeddings, stores them in Qdrant, and enables intelligent chat-based querying through a FastAPI backend and Streamlit frontend. It demonstrates modern AI/ML architecture patterns for enterprise-level document understanding and question-answering systems.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ User Interface (Streamlit UI - Port 8501)                   │
│ • Upload documents/media                                    │
│ • Chat interface with session management                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Requests
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Backend (Port 8000)                                 │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ API Router                                                ││
│ │ • /api/v1/ingest/file  → Ingestion Pipeline             ││
│ │ • /api/v1/chat/message → Conversation Service           ││
│ │ • /api/v1/chat/stream  → Streaming Response             ││
│ │ • /api/v1/docs/*       → Document Management            ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────┬──────────────────────────┬────────────────────┘
              │                          │
     ┌────────▼─────────┐      ┌────────▼─────────┐
     │ Ingestion        │      │ Conversation     │
     │ Pipeline         │      │ Service          │
     └────────┬─────────┘      └────────┬─────────┘
              │                         │
     ┌────────▼────────────────────────┴──────────┐
     │                                             │
     ▼                                             ▼
┌────────────────────────┐          ┌─────────────────────────┐
│ Vector Store (Qdrant)  │          │ LLM Gateway (OpenAI)    │
│ • Stores embeddings    │          │ • gpt-3.5-turbo         │
│ • Enables similarity   │          │ • Retry logic (Tenacity)│
│   search               │          │ • Streaming support     │
└────────────────────────┘          └─────────────────────────┘
```

---

## Detailed Workflows

### Flow 1: Ingestion Pipeline (Document Processing & Indexing)

```
1. FILE UPLOAD
   ├─ User uploads file via Streamlit UI
   ├─ Endpoint: POST /api/v1/ingest/file
   └─ Response: task_id + PENDING status (HTTP 202 Accepted)

2. BACKGROUND PROCESSING
   ├─ File content validated (MIME type detection via `filetype` library)
   └─ Route to appropriate processor:

   A) MEDIA PROCESSOR (PDFs & Images)
      ├─ PDF: PyMuPDF extracts text page-by-page
      │  └─ Fallback: If page has no text, EasyOCR performs OCR
      └─ Images: EasyOCR extracts text

   B) AUDIO/VIDEO PROCESSOR
      ├─ Write file to temporary location
      ├─ OpenAI Whisper transcribes audio/video to text
      │  • Uses "tiny" model for speed (configurable)
      │  • Detects GPU/CPU availability automatically
      ├─ Segments transcription with timestamps
      └─ Create document per segment

3. TEXT CHUNKING
   ├─ LangChain's RecursiveCharacterTextSplitter
   ├─ Default: chunk_size=1000, chunk_overlap=200
   ├─ Splits recursively on sentences/words to maintain context
   └─ Preserves metadata (filename, page, timestamps)

4. EMBEDDING GENERATION
   ├─ Model: Sentence-Transformers "all-MiniLM-L6-v2" (local)
   ├─ Dimension: 384-dimensional vectors
   ├─ Process: Batch encode all chunks
   └─ Output: Dense vectors for semantic similarity

5. VECTOR DATABASE STORAGE
   ├─ Qdrant collection: "rag_collection"
   ├─ Upsert points with:
   │  ├─ Vector: embedding
   │  ├─ Payload (metadata): filename, file_type, page_number, extraction_method, category
   │  └─ ID: Deterministic hash-based UUID (idempotent)
   └─ Create indexed fields for filtering (e.g., source_filename)
```

**Key Technologies:**
- **PyMuPDF (fitz)**: PDF text extraction
- **EasyOCR**: Optical character recognition (pure Python, no binary deps)
- **OpenAI Whisper**: Speech-to-text transcription
- **Sentence-Transformers**: Local embedding model
- **Qdrant**: Vector database with filtering & similarity search

---

### Flow 2: RAG Retrieval & Generation (Question Answering)

```
1. USER QUERY
   ├─ Endpoint: POST /api/v1/chat/message or /api/v1/chat/stream
   ├─ Request includes: query, session_id, model, temperature, top_k, use_reranker
   └─ Session management: Creates new session if none provided

2. QUERY EMBEDDING
   ├─ Embed user query using same model as ingestion
   ├─ Output: Single 384-dimensional vector
   └─ Purpose: Find semantically similar documents

3. VECTOR SEARCH (RETRIEVAL)
   ├─ Search in Qdrant collection
   ├─ Fetch top_k * 3 candidates (e.g., 9 for top_k=3)
   ├─ Distance metric: COSINE similarity
   ├─ Optional filters: On filename, category, file_type (from request)
   └─ Return: candidate_k results with scores & metadata

4. RERANKING (OPTIONAL)
   ├─ Model: Sentence-Transformers Cross-Encoder
   ├─ Purpose: Re-score candidates by semantic relevance to query
   ├─ Output: Top-K final results (default: 3)
   └─ Benefits: Improves answer quality, reduces noise

5. PROMPT CONSTRUCTION
   ├─ System Message:
   │  └─ "You are a helpful expert assistant in Multimodal RAG..."
   │  └─ "Answer based ONLY on provided context..."
   │  └─ "Cite sources using [Source: filename]"
   │
   ├─ Context Assembly:
   │  ├─ Format each retrieved result with source metadata
   │  ├─ Include: filename, page number, timestamp (if audio/video)
   │  └─ Join as formatted context block
   │
   ├─ Chat History:
   │  ├─ Memory Manager maintains session history
   │  ├─ Last 10 turns included (sliding window)
   │  └─ Avoids exceeding context window limits
   │
   └─ Current Query:
      └─ Appended as user message

6. LLM GENERATION
   ├─ LLM Gateway (OpenAI provider)
   ├─ Model: gpt-3.5-turbo (configurable)
   ├─ Temperature: Default 0.7 (for balanced creativity/consistency)
   ├─ Retry Logic:
   │  ├─ Tenacity library with exponential backoff
   │  ├─ Max 3 attempts
   │  ├─ Handles: APIConnectionError, RateLimitError
   │  └─ Wait: 2-10s between retries
   └─ Response Mode:
      ├─ Non-streaming: Return full response
      └─ Streaming: Yield chunks token-by-token

7. RESPONSE & MEMORY UPDATE
   ├─ Stream response back to Streamlit UI
   ├─ Add user query → conversation memory
   ├─ Add assistant response → conversation memory
   ├─ Audit logging: Query, response, latency
   └─ Metrics tracking: LLM latency, token usage

8. SESSION MANAGEMENT
   ├─ Sessions persist across queries
   ├─ History enables multi-turn conversations
   ├─ Endpoint: GET /api/v1/chat/history/{session_id}
   └─ Returns: List of ChatMessages (role + content)
```

**Key Technologies:**
- **FastAPI**: Async request handling, streaming responses
- **Tenacity**: Robust retry logic with backoff
- **OpenAI Python SDK**: LLM integration with streaming
- **Qdrant Client**: Vector search with filtering
- **Sentence-Transformers**: Cross-Encoder reranking

---

## Core Concepts & Technologies

### 1. Retrieval-Augmented Generation (RAG)
- **Problem**: LLMs have fixed knowledge cutoff; hallucinate on domain-specific queries
- **Solution**: Retrieve relevant documents first, augment LLM prompt with context
- **Implementation**: Query embedding → vector search → context assembly → LLM generation
- **Benefits**: Reduces hallucinations, enables Q&A on custom documents, cost-effective

### 2. Vector Embeddings & Semantic Search
- **Embeddings**: Dense numerical representations of text (384 dimensions for all-MiniLM-L6-v2)
- **Semantic Similarity**: COSINE distance measures meaning closeness (not keyword matching)
- **Why Local Model**: `all-MiniLM-L6-v2` is lightweight (~80MB), inference is instant, no API calls
- **Trade-off**: Smaller model = faster, but less nuanced than OpenAI's `text-embedding-3-large`

### 3. Vector Database (Qdrant)
- **Purpose**: Stores vectors + metadata, enables fast similarity search
- **Alternative Models**: Pinecone (cloud), Weaviate, Milvus
- **Key Features Used**:
  - Payload indexing for fast filtering
  - Cosine distance metric for semantic similarity
  - In-memory option for development (`path=./qdrant_data`)
  - Cloud option for production (`url=https://...`)

### 4. Document Chunking Strategy
- **Why**: Embeddings work best on moderate-length chunks (~500-1000 tokens)
- **Overlapping Chunks**: Preserve context at boundaries (200 char overlap)
- **LangChain's RecursiveCharacterTextSplitter**: Splits on sentences/words (not random characters)
- **Preservation**: Metadata (filename, page) travels with each chunk

### 5. Multimodal Processing

| Format | Technology | Output | Notes |
|--------|-----------|--------|-------|
| **PDF** | PyMuPDF | Page text | Fallback to EasyOCR if text-less |
| **Images** | EasyOCR | Extracted text | Pure Python, GPU-optional |
| **Audio** | OpenAI Whisper | Transcription + segments | "tiny" model for speed |
| **Video** | OpenAI Whisper | Transcription + timestamps | Processes audio stream from video |

### 6. Reranking
- **Stage 1 Retrieval**: BM25 or vector search (fast, retrieves ~9 candidates)
- **Stage 2 Reranking**: Cross-Encoder scores candidates for query-relevance (slower, precise)
- **Why**: Improves top-K quality without querying entire database
- **Cost-Benefit**: Minimal inference cost for quality gains

### 7. Session Management & Memory
- **Stateful Conversations**: Session IDs track multi-turn context
- **Chat History**: In-memory MemoryManager stores last N turns
- **Sliding Window**: Prevents context overflow, maintains conversation flow
- **Persistence**: Optional (could integrate with Redis/DB for production)

### 8. Production Features

| Feature | Implementation | Purpose |
|---------|-----------------|---------|
| **Health Checks** | `/health`, `/readiness`, `/liveness` | Kubernetes probes |
| **Async Processing** | BackgroundTasks in FastAPI | Non-blocking file uploads |
| **Rate Limiting** | SlowAPI middleware | Prevent abuse |
| **Observability** | OpenTelemetry + Prometheus | Distributed tracing, metrics |
| **Audit Logging** | Dedicated audit_logger | Compliance, debugging |
| **Token Tracking** | Usage metrics from LLM | Cost monitoring |
| **Error Handling** | Tenacity retry decorator | Resilience to transient failures |

---

## Project Structure Deep Dive

```
app/
├── main.py                           # FastAPI app initialization, lifespan hooks
├── core/
│   ├── config.py                     # Pydantic Settings (env vars, defaults)
│   ├── logging.py                    # Structured logging setup
│   └── middleware.py                 # Request logging middleware
│
├── api/v1/
│   ├── api.py                        # Router aggregation
│   └── endpoints/
│       ├── ingestion.py              # POST /ingest/file → background task
│       ├── chat.py                   # POST /chat/message, /chat/stream
│       └── documents.py              # Document listing/management
│
├── ingestion/
│   ├── service.py                    # Orchestrates file→chunks→embeddings→storage
│   ├── models.py                     # Document, IngestionMetadata, IngestionResponse
│   ├── chunker.py                    # RecursiveCharacterTextSplitter wrapper
│   └── processors/
│       ├── base.py                   # Abstract BaseProcessor
│       ├── media.py                  # PDF + Image handler (PyMuPDF, EasyOCR)
│       └── av.py                     # Audio/Video handler (Whisper + FFmpeg)
│
├── llm/
│   ├── embedding_service.py          # Embedding model factory & interface
│   ├── conversation_service.py       # Orchestrates retrieve→prompt→generate
│   ├── gateway.py                    # LLM provider abstraction (OpenAI, Mock)
│   ├── prompt_builder.py             # Constructs system + context + history
│   └── providers/
│       ├── base.py                   # Abstract LLMProvider
│       ├── openai.py                 # OpenAI API client wrapper
│       └── mock.py                   # For testing (no API calls)
│
├── db/
│   └── vector_store_client.py        # Qdrant integration (search, upsert)
│
├── retrieval/
│   ├── retriever.py                  # Orchestrates embed→search→rerank
│   ├── reranker.py                   # Cross-Encoder reranking logic
│   └── models.py                     # RetrievalQuery, SearchResult, RetrievalResponse
│
├── memory/
│   └── manager.py                    # Session storage, chat history, ChatMessage model
│
└── observability/
    ├── telemetry.py                  # OpenTelemetry setup
    ├── metrics.py                    # Prometheus metrics (LLM_LATENCY, etc.)
    └── audit_logger.py               # Audit trail logging

ui/
└── app.py                            # Streamlit interface
    ├── File upload widget
    ├─ Chat interface with session persistence
    └─ Display sources & citations
```

---

## Technology Stack

### Backend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI | Modern async web framework, auto OpenAPI docs |
| **Server** | Uvicorn | ASGI server, supports streaming |
| **Request Validation** | Pydantic v2 | Type-safe request/response models |
| **Config Management** | Pydantic Settings + python-dotenv | Environment-based configuration |
| **Task Queue** | BackgroundTasks (FastAPI) | Async file processing without celery overhead |

### Data Processing

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **PDF** | PyMuPDF (fitz) | Fast text extraction |
| **Images** | EasyOCR, Pillow | OCR without Tesseract binary dependency |
| **Audio/Video** | OpenAI Whisper | SOTA speech-to-text |
| **Text Splitting** | LangChain TextSplitters | Semantic-aware chunking |
| **Embeddings** | Sentence-Transformers | Lightweight, local embedding model |

### AI/ML

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Vector DB** | Qdrant | Fast similarity search on embeddings |
| **Reranking** | Cross-Encoder (transformers) | Improve retrieval precision |
| **LLM Provider** | OpenAI API | GPT-3.5-Turbo generation + streaming |
| **Retry Logic** | Tenacity | Resilience to transient API failures |

### Observability

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Tracing** | OpenTelemetry | Distributed tracing across services |
| **Metrics** | Prometheus Client | Latency, token usage tracking |
| **Logging** | Python logging + JSON | Structured, auditable logs |

### Frontend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI** | Streamlit | Rapid prototyping, interactive widgets |
| **HTTP Client** | requests library | Call backend API |
| **State** | Streamlit session state | Multi-turn conversation tracking |

### Deployment

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Containerization** | Docker | Consistent environments |
| **Orchestration** | Docker Compose | Local multi-container setup |
| **Python Version** | 3.11-slim | Lightweight, recent standard library |

---

## Key Algorithms & Techniques

### 1. Recursive Character Text Splitting

```
Input: Long document (e.g., 50KB paper)
↓
Split on: ["\n\n", "\n", " ", ""]  (recursive, order matters)
↓
Parameters:
  - chunk_size = 1000 chars
  - overlap = 200 chars
↓
Output: Overlapping chunks preserving semantic boundaries
Why: Avoids breaking sentences mid-thought; maintains context.
```

### 2. Cosine Similarity for Embeddings

```
Query Vector: [0.1, 0.5, 0.3, ...]  (384 dims)
Document Vector: [0.12, 0.48, 0.32, ...]
↓
Cosine Similarity = (Query · Document) / (||Query|| * ||Document||)
Range: -1 to 1 (closer to 1 = more similar)
↓
Qdrant returns top-K by similarity score
```

### 3. Two-Stage Retrieval with Reranking

```
Stage 1 (Fast Recall):
  User Query → Embed → Vector Search → Get 9 candidates

Stage 2 (High Precision):
  Cross-Encoder scores 9 candidates against query
  → Selects top 3 by semantic relevance
  
Why two-stage?
  - Stage 1 is fast (index lookup)
  - Stage 2 is thorough (pairwise scoring)
  - Total cost = retrieval + light reranking ≈ single direct search
```

### 4. Chain-of-Thought Prompt Engineering

```
SYSTEM: "You are a helpful assistant. Answer based ONLY on context..."
↓
CONTEXT: Retrieved chunks with sources
↓
HISTORY: Last 10 chat turns
↓
USER: Current query
↓
Model generates response with citations
```

### 5. Exponential Backoff Retry

```
Attempt 1: Fail with RateLimitError
  → Wait 2s, retry

Attempt 2: Fail with APIConnectionError
  → Wait 4-6s (random), retry

Attempt 3: Fail again
  → Raise exception

Why: Transient failures (rate limits, network hiccups) resolve quickly.
```

---

## Interview Talking Points

### Architecture Decisions

1. **Why Qdrant over Elasticsearch?**
   - Specialized for vector search (not full-text)
   - Native cosine distance metric
   - Simpler API, lower ops overhead
   - Milvus alternative: more scalable for billions of vectors

2. **Why Local Embedding Model?**
   - Speed: Inference <10ms (vs. API calls ~100ms)
   - Cost: Free, on-premises
   - Trade-off: Smaller model (~384 dims vs OpenAI's 1536)
   - Could upgrade to `all-mpnet-base-v2` (768 dims) for better quality

3. **Why Two-Stage Retrieval?**
   - Precision: Reranking improves top-3 quality
   - Cost-effective: Light second stage vs. larger first-stage retrieval
   - Scalability: Can retrieve broadly, rerank narrowly

4. **Multimodal Processing Strategy**
   - OCR for static media (PDF, images)
   - Speech-to-text for dynamic media (audio, video)
   - All outputs unified as text → standard RAG pipeline
   - Avoids separate vision models for initial PoC

### Scalability Considerations

| Bottleneck | Current | Production Fix |
|------------|---------|-----------------|
| **Memory** | In-memory chat history | Redis/PostgreSQL |
| **Throughput** | Single FastAPI worker | Kubernetes deployment, load balancing |
| **Storage** | Vector DB on single host | Qdrant cluster mode |
| **Ingestion** | BackgroundTasks | Celery + message queue for heavy workloads |
| **Embedding** | Single GPU (if available) | Batch processing, GPU clusters |

### Security & Compliance

- **API Keys**: Stored in `.env`, never committed (good)
- **Audit Logging**: Tracks queries & responses (compliance-ready)
- **User Auth**: Not implemented (assume OAuth2 in production)
- **Data Privacy**: Vector storage metadata could contain PII (needs masking)

### Error Handling

- **Unsupported File Types**: Graceful rejection with 500 error
- **Missing Dependencies**: FFmpeg/Tesseract warnings, clear error messages
- **LLM Failures**: Retry logic + human-readable error responses
- **Vector DB Offline**: Health checks fail, prevents ingestion

---

## Running the System

### Local Setup

```bash
# 1. Start Qdrant
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant:latest

# 2. Start FastAPI backend
uvicorn app.main:app --reload --port 8000

# 3. Start Streamlit UI
streamlit run ui/app.py
```

### Docker Compose (All-in-one)

```bash
docker-compose up --build
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Upload file
curl -X POST -F "file=@sample.pdf" http://localhost:8000/api/v1/ingest/file

# Chat
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the document about?", "top_k": 3}'
```

---

## Common Interview Questions & Answers

### Q: How do you handle documents larger than context window?
**A:** Recursive chunking with overlap + retrieval pipeline. Only top-K chunks enter LLM context, managed by sliding window (last 10 turns).

### Q: Why not fine-tune the embedding model?
**A:** All-MiniLM-L6-v2 generalizes well across domains. For specialized content, could fine-tune, but adds complexity & inference overhead.

### Q: How do you prevent hallucinations?
**A:** (1) System prompt enforces context-only answers, (2) Streaming lets users see real-time generation, (3) Citation requirement, (4) Reranking improves retrieval accuracy.

### Q: What if a query has no relevant documents?
**A:** Prompt explicitly says "If no answer in context, say 'I don't have enough information...'" Model is coached to reject, not hallucinate.

### Q: Scaling to 1M documents?
**A:** Qdrant supports partitioning & sharding. Ingestion would move to Celery queue. Embedding batching critical (GPU bottleneck).

### Q: How do you handle streaming responses efficiently?
**A:** FastAPI's StreamingResponse + OpenAI SDK's streaming. Chunks are yielded as they arrive, reducing latency perception & enabling cancellation.

### Q: What's the difference between your local embedding model and OpenAI's?
**A:** Local (384 dims, all-MiniLM-L6-v2): faster, free, on-premises. OpenAI (1536 dims, text-embedding-3-large): more nuanced, requires API calls. Trade-off: speed vs. quality.

### Q: How does reranking improve results?
**A:** Vector search is fast but may miss context-specific relevance. Cross-Encoders score query-document pairs directly, catching semantic nuances vector search misses.

### Q: How would you handle real-time document updates?
**A:** Implement versioning in metadata, mark old chunks deprecated, re-ingest with new IDs. Optional: Incremental indexing on source changes (file watch + delta processing).

### Q: What monitoring/observability would you add for production?
**A:** (1) OpenTelemetry traces through ingestion/retrieval/LLM, (2) Prometheus metrics for latency/errors, (3) Audit logs for compliance, (4) SLO tracking (P99 latency, error rates).

---

## Conclusion

This Multimodal RAG pipeline demonstrates:
- **Modern ML architecture**: RAG, vector search, semantic similarity
- **Production readiness**: Error handling, logging, observability, health checks
- **Scalability thinking**: Async processing, two-stage retrieval, pluggable components
- **Multimodal capability**: Unified text extraction from diverse media types
- **Clean engineering**: Modular design, abstract interfaces, config management

Perfect for discussing AI systems design, ML engineering trade-offs, and production considerations in interviews.
