from fastapi import APIRouter
from app.api.v1.endpoints import ingestion, chat, documents

api_router = APIRouter()
api_router.include_router(ingestion.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(documents.router, prefix="/docs", tags=["Documents"])
