import logging
import os
from typing import List, Dict, Union, AsyncGenerator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

from app.llm.providers.base import LLMProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.providers.mock import MockProvider
from app.memory.manager import ChatMessage

logger = logging.getLogger(__name__)

from app.core.config import get_settings

settings = get_settings()

class LLMGateway:
    def __init__(self, provider_name: str = "openai"):
        self.provider: LLMProvider = self._get_provider(provider_name)
        
    def _get_provider(self, name: str) -> LLMProvider:
        if name == "openai":
            api_key = settings.OPENAI_API_KEY
            base_url = settings.LLM_BASE_URL
            
            # Strict check
            if not api_key:
                logger.error("OPENAI_API_KEY is missing in settings!")
                raise ValueError("OPENAI_API_KEY is required.")
                
            return OpenAIProvider(api_key=api_key, base_url=base_url, model=settings.LLM_MODEL)
        elif name == "mock":
            return MockProvider()
        else:
            raise ValueError(f"Unknown provider: {name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIConnectionError, openai.RateLimitError)),
        reraise=True
    )
    async def generate_response(self, messages: List[ChatMessage], **kwargs):
        """
        Generates a response with retry logic and unified monitoring.
        """
        # Convert internal ChatMessage model to provider dict format
        msgs_dicts = [{"role": m.role.value, "content": m.content} for m in messages]
        
        try:
            response = await self.provider.generate_response(msgs_dicts, **kwargs)
            
            # Simple Cost Tracking Hook
            self._track_usage(response.usage)
            
            return response.content
            
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            raise

    async def stream_response(self, messages: List[ChatMessage], **kwargs):
        """
        Streams response with retry logic.
        """
        msgs_dicts = [{"role": m.role.value, "content": m.content} for m in messages]
        
        try:
            async for chunk in self.provider.stream_response(msgs_dicts, **kwargs):
                if not chunk.content: 
                    # Sometimes empty chunks come for finish reasons, which is fine
                    continue
                yield chunk.content
        except Exception as e:
            logger.error(f"LLM Streaming Failed: {e}", exc_info=True)
            yield f"\n[System Error: LLM Streaming Failed - {str(e)}]"
            raise

    def _track_usage(self, usage):
        logger.info(f"Token Usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
