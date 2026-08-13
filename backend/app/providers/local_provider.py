"""Local OpenAI-compatible endpoint (e.g. Ollama)."""

import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProvider, LLMProviderError
from app.utils.json_extract import extract_json_object


class LocalProvider(LLMProvider):
    def name(self) -> str:
        return "local"

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        settings = get_settings()
        url = f"{settings.local_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": "Bearer local",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.local_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system + "\nRespond with JSON only."},
                {"role": "user", "content": user},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMProviderError("Local model request timed out.", 504) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError("Could not reach local model endpoint.", 502) from exc

        if response.status_code >= 400:
            raise LLMProviderError("Local model request failed.", 502)

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Malformed local model response.", 502) from exc

        try:
            return extract_json_object(content)
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMProviderError("Local model returned invalid JSON.", 502) from exc
