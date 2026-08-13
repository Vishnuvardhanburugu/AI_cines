"""Image generation provider interface and router."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.core.config import get_settings
from app.providers.base import LLMProviderError


@dataclass
class ImageResult:
    image_url: str
    provider: str
    prompt_used: str


class ImageProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 576,
    ) -> ImageResult:
        ...

    @abstractmethod
    def name(self) -> str:
        ...


def truncate_image_prompt(prompt: str, max_len: Optional[int] = None) -> str:
    settings = get_settings()
    limit = max_len or settings.image_max_prompt_length
    cleaned = " ".join(prompt.split()).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def get_image_provider(force: Optional[str] = None) -> ImageProvider:
    settings = get_settings()
    name = (force or settings.image_provider or "auto").lower()

    if name == "mock":
        from app.providers.mock_image import MockImageProvider

        return MockImageProvider()
    if name == "pollinations":
        from app.providers.pollinations_image import PollinationsImageProvider

        return PollinationsImageProvider()
    if name == "gemini":
        from app.providers.gemini_image import GeminiImageProvider

        return GeminiImageProvider()
    if name == "auto":
        from app.providers.auto_image import AutoImageProvider

        return AutoImageProvider()

    raise LLMProviderError(f"Unsupported image provider: {name}", status_code=400)
