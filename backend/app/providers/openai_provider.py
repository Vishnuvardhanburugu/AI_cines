"""OpenAI-compatible chat completions provider."""

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProvider, LLMProviderError
from app.utils.json_extract import extract_json_object


class OpenAIProvider(LLMProvider):
    def name(self) -> str:
        return "openai"

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        settings = get_settings()
        if not settings.openai_api_key:
            raise LLMProviderError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY in the backend environment.",
                status_code=503,
            )

        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                "The language model request timed out. Please try again.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(
                "Could not reach the language model provider.",
                status_code=502,
            ) from exc

        if response.status_code == 429:
            raise LLMProviderError(
                "Rate limit reached with the language model provider. Please wait and retry.",
                status_code=429,
            )
        if response.status_code >= 500:
            raise LLMProviderError(
                "Language model provider is temporarily unavailable.",
                status_code=502,
            )
        if response.status_code >= 400:
            raise LLMProviderError(
                "Language model request was rejected. Check configuration and try again.",
                status_code=502,
            )

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "Malformed response from the language model provider.",
                status_code=502,
            ) from exc

        try:
            return extract_json_object(content)
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMProviderError(
                "Model returned invalid JSON. Please try again.",
                status_code=502,
            ) from exc
