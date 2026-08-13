"""xAI Grok provider (OpenAI-compatible Chat Completions API).

Note: Free Grok on X/grok.com is not the same as free API access.
"""

import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProvider, LLMProviderError
from app.utils.json_extract import extract_json_object


class GrokProvider(LLMProvider):
    def name(self) -> str:
        return "grok"

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        settings = get_settings()
        if not settings.xai_api_key:
            raise LLMProviderError(
                "xAI/Grok API key is not configured. Set XAI_API_KEY. "
                "Note: free Grok chat on X is not a free developer API.",
                status_code=503,
            )

        url = f"{settings.xai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.xai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.xai_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": system + "\nRespond with a single valid JSON object only.",
                },
                {"role": "user", "content": user},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMProviderError("The Grok request timed out. Please try again.", 504) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError("Could not reach the xAI/Grok API.", 502) from exc

        if response.status_code == 429:
            raise LLMProviderError("Grok rate limit reached. Please wait and retry.", 429)
        if response.status_code >= 400:
            raise LLMProviderError("Grok request failed. Check XAI_API_KEY and billing.", 502)

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Malformed Grok response.", 502) from exc

        try:
            return extract_json_object(content)
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMProviderError("Grok returned invalid JSON. Please try again.", 502) from exc
