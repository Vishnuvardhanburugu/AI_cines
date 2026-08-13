"""Hugging Face Inference text-to-image (needs HF_API_TOKEN)."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.image_base import ImageProvider, ImageResult, truncate_image_prompt


def _snap_dim(value: int, multiple: int = 16) -> int:
    return max(multiple, (int(value) // multiple) * multiple)


class HuggingFaceImageProvider(ImageProvider):
    def name(self) -> str:
        return "huggingface"

    async def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 576,
    ) -> ImageResult:
        settings = get_settings()
        token = (settings.hf_api_token or "").strip()
        if not token:
            raise LLMProviderError(
                "Hugging Face token is not configured. Create one at "
                "https://huggingface.co/settings/tokens (enable Inference), "
                "set HF_API_TOKEN on the server, restart, then retry. "
                "Or switch to Pollinations (no key).",
                status_code=503,
            )

        used = truncate_image_prompt(prompt, max_len=1800)
        model = settings.hf_image_model.strip()
        w, h = _snap_dim(width), _snap_dim(height)

        # Prefer router; fall back to classic inference URL if needed.
        urls = [
            f"https://router.huggingface.co/hf-inference/models/{model}",
            f"https://api-inference.huggingface.co/models/{model}",
        ]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "image/png",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "inputs": used,
            "parameters": {
                "width": w,
                "height": h,
                "num_inference_steps": 4,
            },
        }

        last_error = "Hugging Face image request failed."
        async with httpx.AsyncClient(timeout=settings.image_timeout_seconds) as client:
            for url in urls:
                try:
                    response = await client.post(url, headers=headers, json=payload)
                except httpx.TimeoutException as exc:
                    raise LLMProviderError(
                        "Hugging Face image generation timed out. Please try again.",
                        504,
                    ) from exc
                except httpx.RequestError:
                    last_error = "Could not reach Hugging Face inference API."
                    continue

                if response.status_code == 401:
                    raise LLMProviderError(
                        "Hugging Face rejected the token. Check HF_API_TOKEN and "
                        "that it has Inference / Inference Providers permission.",
                        401,
                    )
                if response.status_code == 429:
                    raise LLMProviderError(
                        "Hugging Face rate limit reached. Wait and retry, or use Pollinations.",
                        429,
                    )
                if response.status_code == 503:
                    # Model cold-start — one retry on same URL
                    try:
                        response = await client.post(url, headers=headers, json=payload)
                    except httpx.HTTPError:
                        last_error = "Hugging Face model is loading. Retry in a few seconds."
                        continue

                if response.status_code >= 400:
                    detail = ""
                    try:
                        detail = str(response.json())[:220]
                    except Exception:
                        detail = response.text[:220]
                    last_error = (
                        f"Hugging Face image failed ({response.status_code}). "
                        f"Model: {model}. {detail}"
                    )
                    # Try next endpoint URL
                    continue

                content_type = response.headers.get("content-type", "")
                body = response.content
                if not body:
                    last_error = "Hugging Face returned an empty image body."
                    continue
                if "application/json" in content_type:
                    last_error = f"Hugging Face returned JSON instead of an image: {body[:220]!r}"
                    continue

                mime = "image/png"
                if "jpeg" in content_type or "jpg" in content_type:
                    mime = "image/jpeg"
                elif "webp" in content_type:
                    mime = "image/webp"

                b64 = base64.b64encode(body).decode("ascii")
                return ImageResult(
                    image_url=f"data:{mime};base64,{b64}",
                    provider=self.name(),
                    prompt_used=used,
                )

        raise LLMProviderError(last_error, 502)
