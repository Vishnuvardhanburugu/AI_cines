"""Provider interface and factory."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.config import get_settings


class LLMProviderError(Exception):
    """Raised when an LLM provider call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class LLMProvider(ABC):
    @abstractmethod
    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Return parsed JSON object from the model."""

    @abstractmethod
    def name(self) -> str:
        ...


def get_provider(force: Optional[str] = None) -> LLMProvider:
    settings = get_settings()
    provider_name = (force or settings.llm_provider).lower()

    if provider_name == "mock":
        from app.providers.mock import MockProvider

        return MockProvider()
    if provider_name == "openai":
        from app.providers.openai_provider import OpenAIProvider

        return OpenAIProvider()
    if provider_name == "anthropic":
        from app.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if provider_name == "gemini":
        from app.providers.gemini_provider import GeminiProvider

        return GeminiProvider()
    if provider_name in {"grok", "xai"}:
        from app.providers.grok_provider import GrokProvider

        return GrokProvider()
    if provider_name == "local":
        from app.providers.local_provider import LocalProvider

        return LocalProvider()

    raise LLMProviderError(f"Unsupported LLM provider: {provider_name}")
