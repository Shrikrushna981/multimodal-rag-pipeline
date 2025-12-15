from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any, Union
from pydantic import BaseModel

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class LLMResponse(BaseModel):
    content: str
    usage: TokenUsage

class LLMStreamChunk(BaseModel):
    content: str
    finish_reason: Union[str, None] = None

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        pass
