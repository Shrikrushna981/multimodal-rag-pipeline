import os

class UIConfig:
    API_BASE_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    PAGE_TITLE = "Enterprise Multimodal RAG"
    PAGE_ICON = "🤖"
    
    @classmethod
    def get_ingest_url(cls):
        return f"{cls.API_BASE_url}/ingest/file"
    
    @classmethod
    def get_chat_url(cls):
        return f"{cls.API_BASE_url}/chat/message"

    @classmethod
    def get_chat_stream_url(cls):
        return f"{cls.API_BASE_url}/chat/stream"

    API_KEY = os.getenv("RAG_API_KEY", None)

config = UIConfig()
