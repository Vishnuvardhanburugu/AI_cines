"""Google Gemini generateContent provider."""

import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProvider, LLMProviderError
from app.utils.json_extract import extract_json_object


class GeminiProvider(LLMProvider):
    def name(self) -> str:
        return "gemini"

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise LLMProviderError(
                "Gemini API key is not configured. Set GEMINI_API_KEY.",
                status_code=503,
            )

        model = settings.gemini_model
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system + "\nRespond with JSON only."}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMProviderError("The language model request timed out.", 504) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError("Could not reach Gemini.", 502) from exc

        if response.status_code == 429:
            raise LLMProviderError("Gemini rate limit reached.", 429)
        if response.status_code >= 400:
            raise LLMProviderError("Gemini request failed.", 502)

        data = response.json()
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Malformed Gemini response.", 502) from exc

        try:
            return extract_json_object(content)
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMProviderError("Model returned invalid JSON.", 502) from exc
