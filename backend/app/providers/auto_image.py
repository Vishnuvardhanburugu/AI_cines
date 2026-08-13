"""Auto image router: Gemini if key present, else Pollinations; fallback on Gemini failure."""

from __future__ import annotations

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.gemini_image import GeminiImageProvider
from app.providers.image_base import ImageProvider, ImageResult
from app.providers.pollinations_image import PollinationsImageProvider
from app.utils.logging import logger


class AutoImageProvider(ImageProvider):
    def name(self) -> str:
        return "auto"

    async def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 576,
    ) -> ImageResult:
        settings = get_settings()
        pollinations = PollinationsImageProvider()

        if settings.gemini_api_key:
            try:
                return await GeminiImageProvider().generate(
                    prompt, width=width, height=height
                )
            except LLMProviderError as exc:
                logger.info(
                    "Gemini image failed (%s); falling back to Pollinations",
                    exc.message,
                )
                result = await pollinations.generate(prompt, width=width, height=height)
                # Keep provider label honest for UI warning
                return ImageResult(
                    image_url=result.image_url,
                    provider="pollinations",
                    prompt_used=result.prompt_used,
                )

        return await pollinations.generate(prompt, width=width, height=height)
