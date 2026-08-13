"""Image generation service."""

from __future__ import annotations

from app.api.schemas import GenerateImageRequest, GenerateImageResponse
from app.core.security import validate_prompt_input
from app.providers.base import LLMProviderError
from app.providers.image_base import get_image_provider
from app.services.prompt_enhancement.image_prompt_packer import (
    is_mythic_epic,
    pack_image_prompt,
    prefer_portrait,
)


async def generate_image(request: GenerateImageRequest) -> GenerateImageResponse:
    prompt = validate_prompt_input(request.prompt)
    width = request.width or 1024
    height = request.height or 576
    aspect = (request.aspect or "auto").lower()

    if aspect == "portrait" or (
        aspect == "auto" and is_mythic_epic(prompt) and height <= width
    ):
        width, height = prefer_portrait(prompt, width, height)
    elif aspect == "landscape":
        width, height = 1024, 576

    if width < 256 or height < 256 or width > 2048 or height > 2048:
        raise LLMProviderError(
            "Image size must be between 256 and 2048 pixels.",
            status_code=400,
        )

    portrait = height > width
    packed = pack_image_prompt(prompt, portrait=portrait)

    provider_name = (request.provider or "auto").lower()
    if provider_name not in {"auto", "gemini", "pollinations", "mock"}:
        raise LLMProviderError(
            "Unsupported image provider. Use auto, gemini, or pollinations.",
            status_code=400,
        )

    force = None if provider_name == "auto" else provider_name
    provider = get_image_provider(force)
    result = await provider.generate(packed, width=width, height=height)
    return GenerateImageResponse(
        image_url=result.image_url,
        provider=result.provider,
        prompt_used=result.prompt_used,
    )
