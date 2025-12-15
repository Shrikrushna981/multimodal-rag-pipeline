from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Multimodal RAG Pipeline"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Logger
    LOG_LEVEL: str = "INFO"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_LOCATION: Optional[str] = None 

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    class Config:
        env_file = ".env"
        extra = "ignore" # Explicitly ignore other extra env vars if any

@lru_cache()
def get_settings():
    return Settings()
