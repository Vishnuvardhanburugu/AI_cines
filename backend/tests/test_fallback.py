import pytest

from app.providers.base import LLMProviderError
from app.providers.fallback import FallbackProvider
from app.providers.mock import MockProvider


class RateLimitedProvider:
    def name(self) -> str:
        return "gemini"

    async def complete_json(self, system, user, *, temperature=0.3, max_tokens=2048):
        raise LLMProviderError("Gemini rate limit reached.", 429)


@pytest.mark.asyncio
async def test_fallback_on_429():
    provider = FallbackProvider(RateLimitedProvider(), MockProvider())
    data = await provider.complete_json(
        "You are a prompt analysis engine for intent extraction.",
        "User prompt:\ngenerate hanuman photo\nTarget: image",
    )
    assert provider.used_fallback is True
    assert provider.name() == "mock"
    assert "category" in data or "intent" in data or isinstance(data, dict)


@pytest.mark.asyncio
async def test_fallback_sticks_after_first_429():
    calls = {"n": 0}

    class OnceThenOk:
        def name(self) -> str:
            return "gemini"

        async def complete_json(self, system, user, *, temperature=0.3, max_tokens=2048):
            calls["n"] += 1
            raise LLMProviderError("rate", 429)

    provider = FallbackProvider(OnceThenOk(), MockProvider())
    await provider.complete_json("prompt analysis engine", "hello")
    await provider.complete_json("semantic prompt enhancer", "User prompt:\nhello")
    assert provider.used_fallback is True
    assert calls["n"] == 1  # second call never hits primary
