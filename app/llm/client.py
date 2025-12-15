import os
import openai
from typing import List
from app.memory.manager import ChatMessage, Role

class LLMClient:
    def __init__(self):
        # Assumes OPENAI_API_KEY is set in env
        # Could also point to local models via base_url (e.g. vLLM, Ollama)
        self.client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-mock-key"),
            base_url=os.getenv("LLM_BASE_URL", None) 
        )
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

    async def generate_response(self, messages: List[ChatMessage]) -> str:
        # Convert Pydantic models to dict for API
        msgs_dicts = [{"role": m.role.value, "content": m.content} for m in messages]
        
        try:
            # If mock key, detailed implementation won't work real-time without failure.
            # We'll return a dummy response if we detect a mock condition or handle gracefully.
            if os.getenv("OPENAI_API_KEY") == "sk-mock-key" and not os.getenv("LLM_BASE_URL"):
                return "This is a simulated response. Please set OPENAI_API_KEY to get real answers."

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=msgs_dicts,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
