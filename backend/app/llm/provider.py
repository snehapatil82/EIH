from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        pass

    @abstractmethod
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        context_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        pass

def get_llm_provider() -> LLMProvider:
    provider_type = settings.LLM_PROVIDER.lower()
    
    if provider_type == "openai" and settings.OPENAI_API_KEY:
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL
        )
    elif provider_type == "groq" and settings.GROQ_API_KEY:
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model=settings.GROQ_MODEL
        )
    elif provider_type == "ollama":
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key="ollama",
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            model=settings.OLLAMA_MODEL
        )
    elif provider_type == "anthropic" and settings.ANTHROPIC_API_KEY:
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY
        )
    else:
        from app.llm.mock_provider import HighFidelityMockProvider
        return HighFidelityMockProvider()
