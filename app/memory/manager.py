from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
import time

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    role: Role
    content: str
    timestamp: float = Field(default_factory=time.time)

class SessionMemory(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []

class MemoryManager:
    def __init__(self):
        # simple in-memory store: session_id -> SessionMemory
        # In production this would be Redis
        self._store: Dict[str, SessionMemory] = {}

    def get_history(self, session_id: str) -> List[ChatMessage]:
        if session_id not in self._store:
            return []
        return self._store[session_id].messages

    def add_message(self, session_id: str, message: ChatMessage):
        if session_id not in self._store:
            self._store[session_id] = SessionMemory(session_id=session_id)
        self._store[session_id].messages.append(message)

    def clear_history(self, session_id: str):
        if session_id in self._store:
            del self._store[session_id]
