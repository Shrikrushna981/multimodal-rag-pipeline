# Multimodal RAG

Multimodal RAG is an open-source retrieval-augmented generation (RAG) pipeline for ingesting documents, images, audio, and video; creating embeddings; storing vectors in Qdrant; and querying multimodal content via a FastAPI backend and Streamlit UI.
---

## Table of Contents
- Quick Start
- Features
- Architecture
- Prerequisites
- Environment & Configuration
- Running (local & Docker)
- Usage
- Project Structure
- Screenshots
- Contributing
- License

---

## Quick Start
1. Install system prerequisites (Tesseract OCR, FFmpeg). See `SETUP.md` for Windows installers and PATH instructions.
2. Create a virtual environment and install Python dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Create `.env` in the repository root (example below) and set `OPENAI_API_KEY`.
4. Run a Qdrant instance (Docker recommended) or configure Qdrant Cloud and update `QDRANT_HOST`.
5. Launch backend and UI (commands below).

## Features
- Ingest PDFs, images, audio, and video
- OCR (Tesseract) and speech transcription
- Document chunking, embedding generation, and vector storage
- Vector search powered by Qdrant
- FastAPI backend with modular API endpoints
- Streamlit frontend UI for upload + chat
- Pluggable LLM providers (OpenAI, mock provider)

## Architecture
High-level architecture and flows are documented in the `ARCHITECTURE.md` file.

See: [ARCHITECTURE.md](ARCHITECTURE.md)

## Prerequisites
- Python 3.10+ (virtualenv recommended)
- Tesseract OCR (for OCR on images/PDFs)
- FFmpeg (for audio/video processing)
- Docker (recommended to run Qdrant locally)

Windows installation tips and binary locations are documented in `SETUP.md`.

## Environment & Configuration
Create a `.env` file in the repository root. Minimum required keys:

```
# Core
APP_NAME="Multimodal RAG"
DEBUG=True
LOG_LEVEL=INFO

# LLM Providers
OPENAI_API_KEY=sk-...

# Vector DB
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=multimodal_rag
```

Files of interest:
- `SETUP.md` — system prerequisites and quick setup
- `app/main.py` — FastAPI application entrypoint
- `docker-compose.yaml` — brings up Qdrant + backend + UI (optional)

## Running

### Run Qdrant (Docker)
Run Qdrant locally with Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

### Backend (FastAPI)
Start the API server on port `8000`:

```bash
uvicorn app.main:app --reload --port 8000
```

Health check endpoint:

```bash
curl http://localhost:8000/health
```

### Frontend (Streamlit)
Start the UI on port `8501`:

```bash
streamlit run ui/app.py
```

### Docker Compose (All-in-one)
To run the full stack (Qdrant + backend + UI) using Docker Compose:

```bash
docker-compose up --build
```

If using Qdrant Cloud or an externally hosted Qdrant, set `QDRANT_HOST` and `QDRANT_PORT` in `.env`.

## Usage
1. Open the Streamlit UI at `http://localhost:8501`.
2. Use the sidebar to upload a PDF, image, audio, or video for ingestion.
3. Monitor ingestion logs in the backend; when complete, open the chat and ask questions about the uploaded content.

Key server endpoints (see `app/api/v1/endpoints/`):
- `chat.py` — chat and user queries
- `documents.py` — list/manage documents
- `ingestion.py` — trigger ingestion flows

## Project Structure (top-level)

```
app/                  # FastAPI application and routes
  api/                 # API versioned endpoints
  core/                # config, logging, middleware
  models/              # Pydantic models (if present)
ingestion/            # chunker, processors, ingestion service
llm/                  # LLM client, embedding & prompt builders
db/                   # vector store client (Qdrant integration)
ui/                   # Streamlit frontend
SETUP.md              # setup and prerequisites (Windows notes)
ARCHITECTURE.md       # architecture overview
docker-compose.yaml   # optional all-in-one run
```

## Screenshots
Screenshots are excluded per request. If you later want them added, place images in `docs/screenshots/` and tell me filenames — I will insert them into this README.

## Contributing
Contributions are welcome. Suggested workflow:
1. Fork the repo
2. Create a feature branch (`feature/your-feature`)
3. Open a pull request with a description and relevant tests or examples

If you have preferred linters or formatters, note them in a PR description or issue.

## License
No license is included. This project is provided without a license; reuse and redistribution are not explicitly granted. 

## Contact
For questions or help, open an issue or send a message to the project maintainer.

---

Notes & To-dos:
- [ ] Provide any additional docs, example transcripts, or screenshots later.

