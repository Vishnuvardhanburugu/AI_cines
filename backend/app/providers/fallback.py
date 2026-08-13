"""Primary LLM with automatic mock fallback on rate limits / missing key."""

from typing import Any

from app.providers.base import LLMProvider, LLMProviderError
from app.providers.mock import MockProvider


class FallbackProvider(LLMProvider):
    """Use primary until it hits quota/unavailable, then stick to mock for the request."""

    def __init__(self, primary: LLMProvider, fallback: LLMProvider | None = None):
        self.primary = primary
        self.fallback = fallback or MockProvider()
        self._active: LLMProvider = primary
        self.used_fallback = False

    def name(self) -> str:
        return self._active.name()

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        if self.used_fallback:
            return await self.fallback.complete_json(
                system, user, temperature=temperature, max_tokens=max_tokens
            )

        try:
            return await self.primary.complete_json(
                system, user, temperature=temperature, max_tokens=max_tokens
            )
        except LLMProviderError as exc:
            if exc.status_code in {429, 503} and self.primary.name() != self.fallback.name():
                self.used_fallback = True
                self._active = self.fallback
                return await self.fallback.complete_json(
                    system, user, temperature=temperature, max_tokens=max_tokens
                )
            raise
