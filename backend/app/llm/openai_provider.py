from typing import List, Dict, Any, Optional
import httpx
from app.llm.provider import LLMProvider
from app.core.logging import logger

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if conversation_history:
            for hist in conversation_history:
                if hist.get("role") and hist.get("content"):
                    messages.append({"role": hist["role"], "content": hist["content"]})
        
        full_prompt = prompt
        if context_chunks:
            context_str = "\n\n".join([
                f"--- File: {c.get('file_path')} (Lines {c.get('start_line')}-{c.get('end_line')}) ---\n{c.get('content')}"
                for c in context_chunks
            ])
            full_prompt = f"Relevant Codebase Context:\n{context_str}\n\nUser Request:\n{prompt}"

        messages.append({"role": "user", "content": full_prompt})
        return await self._call_api(messages, temperature)

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        context_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        formatted_messages = list(messages)
        if context_chunks and formatted_messages:
            context_str = "\n\n".join([
                f"--- File: {c.get('file_path')} (Lines {c.get('start_line')}-{c.get('end_line')}) ---\n{c.get('content')}"
                for c in context_chunks
            ])
            # Prepend context to the last user message
            last_msg = formatted_messages[-1]
            if last_msg["role"] == "user":
                formatted_messages[-1] = {
                    "role": "user",
                    "content": f"Repository Context:\n{context_str}\n\nQuestion:\n{last_msg['content']}"
                }

        return await self._call_api(formatted_messages)

    async def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LLM API call failed: {e}")
                raise e
