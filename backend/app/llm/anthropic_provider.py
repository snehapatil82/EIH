from typing import List, Dict, Any, Optional
import httpx
from app.llm.provider import LLMProvider
from app.core.logging import logger

class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com/v1",
        model: str = "claude-3-5-sonnet-20241022"
    ):
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
        return await self._call_api(messages, system_prompt=system_prompt, temperature=temperature)

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        context_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        formatted_messages = []
        system_prompt = None

        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content")
            else:
                formatted_messages.append({
                    "role": "user" if msg.get("role") == "user" else "assistant",
                    "content": msg.get("content", "")
                })

        if context_chunks and formatted_messages:
            context_str = "\n\n".join([
                f"--- File: {c.get('file_path')} (Lines {c.get('start_line')}-{c.get('end_line')}) ---\n{c.get('content')}"
                for c in context_chunks
            ])
            for i in range(len(formatted_messages) - 1, -1, -1):
                if formatted_messages[i]["role"] == "user":
                    formatted_messages[i]["content"] = (
                        f"Repository Context:\n{context_str}\n\nQuestion:\n{formatted_messages[i]['content']}"
                    )
                    break

        return await self._call_api(formatted_messages, system_prompt=system_prompt)

    async def _call_api(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
            "temperature": temperature
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/messages", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content_blocks = data.get("content", [])
                text_outputs = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                return "".join(text_outputs)
            except Exception as e:
                logger.error(f"Anthropic API call failed: {e}")
                raise e
