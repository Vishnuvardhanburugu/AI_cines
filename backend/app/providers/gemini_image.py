"""Gemini image generation (preferred quality path; needs GEMINI_API_KEY)."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.image_base import ImageProvider, ImageResult, truncate_image_prompt


class GeminiImageProvider(ImageProvider):
    def name(self) -> str:
        return "gemini"

    async def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 576,
    ) -> ImageResult:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise LLMProviderError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in backend/.env "
                "(from https://aistudio.google.com/apikey), restart the backend, then retry. "
                "Or switch the image provider to Pollinations for a free lower-quality still.",
                status_code=503,
            )

        used = truncate_image_prompt(prompt, max_len=1800)
        model = settings.gemini_image_model
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={settings.gemini_api_key}"
        )
        aspect = "9:16" if height > width else "1:1" if width == height else "16:9"
        instruction = (
            "You are a photoreal cinematic still photographer for mythological epic cinema. "
            f"Generate ONE still image only, aspect ratio {aspect}. "
            "Prioritize: photoreal live-action textures (fur, metal, fabric, smoke), "
            "dramatic dual lighting (cool moonlight + warm firelight), volumetric atmosphere, "
            "heroic low-angle composition. Strictly avoid cartoon, anime, comic, illustration, "
            "plastic CGI faces, text, logos, watermarks.\n\n"
            f"SCENE PROMPT:\n{used}"
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": instruction}],
                }
            ],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.image_timeout_seconds) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMProviderError("Gemini image generation timed out. Please try again.", 504) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError("Could not reach Gemini image API.", 502) from exc

        if response.status_code == 429:
            raise LLMProviderError(
                "Gemini image rate limit reached. Wait and retry, switch to Hugging Face, "
                "or use Pollinations.",
                429,
            )
        if response.status_code >= 400:
            detail = ""
            try:
                detail = str(response.json())[:200]
            except Exception:
                detail = response.text[:200]
            raise LLMProviderError(
                "Gemini image generation failed. Check GEMINI_API_KEY and that the image model "
                f"({model}) is available on your free/paid tier. Details: {detail}",
                502,
            )

        data = response.json()
        image_b64, mime = _extract_inline_image(data)
        if not image_b64:
            raise LLMProviderError(
                "Gemini returned no image data. Confirm GEMINI_IMAGE_MODEL supports image output.",
                502,
            )

        mime = mime or "image/png"
        return ImageResult(
            image_url=f"data:{mime};base64,{image_b64}",
            provider=self.name(),
            prompt_used=used,
        )


def _extract_inline_image(data: dict[str, Any]) -> tuple[str | None, str | None]:
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return None, None

    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if not inline:
            continue
        b64 = inline.get("data")
        mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
        if b64:
            return b64, mime
    return None, None
