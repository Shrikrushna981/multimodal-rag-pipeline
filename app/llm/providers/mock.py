from typing import List, Dict, AsyncGenerator
from app.llm.providers.base import LLMProvider, LLMResponse, LLMStreamChunk, TokenUsage

class MockProvider(LLMProvider):
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        return LLMResponse(
            content="This is a mocked response because no API key was provided.",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20)
        )

    async def stream_response(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        text = "This is a mocked stream."
        for word in text.split():
            yield LLMStreamChunk(content=word + " ")
        yield LLMStreamChunk(content="", finish_reason="stop")
