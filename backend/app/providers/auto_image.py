"""Auto image router: Gemini → Hugging Face → Pollinations."""

from __future__ import annotations

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.gemini_image import GeminiImageProvider
from app.providers.huggingface_image import HuggingFaceImageProvider
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
                logger.info("Gemini image failed (%s); trying next provider", exc.message)

        if settings.hf_api_token:
            try:
                return await HuggingFaceImageProvider().generate(
                    prompt, width=width, height=height
                )
            except LLMProviderError as exc:
                logger.info(
                    "Hugging Face image failed (%s); falling back to Pollinations",
                    exc.message,
                )

        return await pollinations.generate(prompt, width=width, height=height)
