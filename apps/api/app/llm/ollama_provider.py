import json
from typing import AsyncGenerator

import httpx

from app.core.config import settings
from app.llm.provider import LLMProvider

class OllamaProvider(LLMProvider):
    """
    Ollama integration for local LLMs.
    Connects to the Ollama HTTP API to stream completions.
    """

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Streams a completion from Ollama's /api/generate endpoint.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }

        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("POST", url, json=payload, timeout=None) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
            except httpx.RequestError as e:
                # In a real app we'd want custom exceptions, but yielding an error string
                # or raising a standard exception works for Phase 1.
                raise RuntimeError(f"Error communicating with Ollama: {e}")
