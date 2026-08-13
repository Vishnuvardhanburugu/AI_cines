"""Anthropic Messages API provider stub with real HTTP path when key is set."""

import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProvider, LLMProviderError
from app.utils.json_extract import extract_json_object


class AnthropicProvider(LLMProvider):
    def name(self) -> str:
        return "anthropic"

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise LLMProviderError(
                "Anthropic API key is not configured. Set ANTHROPIC_API_KEY.",
                status_code=503,
            )

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system + "\n\nRespond with a single valid JSON object only.",
            "messages": [{"role": "user", "content": user}],
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMProviderError("The language model request timed out.", 504) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError("Could not reach Anthropic.", 502) from exc

        if response.status_code == 429:
            raise LLMProviderError("Anthropic rate limit reached.", 429)
        if response.status_code >= 400:
            raise LLMProviderError("Anthropic request failed.", 502)

        data = response.json()
        try:
            content = data["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Malformed Anthropic response.", 502) from exc

        try:
            return extract_json_object(content)
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMProviderError("Model returned invalid JSON.", 502) from exc
