import openai
from typing import List, Dict, AsyncGenerator
from app.llm.providers.base import LLMProvider, LLMResponse, LLMStreamChunk, TokenUsage
import os

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo", base_url: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
        self.model = model

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        # Handle model override from kwargs
        model = kwargs.pop("model", self.model)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
        )

    async def stream_response(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        # Handle model override from kwargs
        model = kwargs.pop("model", self.model)
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            finish_reason = chunk.choices[0].finish_reason
            yield LLMStreamChunk(content=content, finish_reason=finish_reason)
