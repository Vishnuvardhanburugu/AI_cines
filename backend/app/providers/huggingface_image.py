"""Hugging Face Inference Providers text-to-image (needs HF_API_TOKEN)."""

from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.image_base import ImageProvider, ImageResult, truncate_image_prompt


def _snap_dim(value: int, multiple: int = 16) -> int:
    return max(multiple, (int(value) // multiple) * multiple)


def extract_image_url_from_json(data: Any) -> str | None:
    """Pull an image URL or data URI from common HF / Fal JSON shapes."""
    if isinstance(data, str) and (
        data.startswith("http://")
        or data.startswith("https://")
        or data.startswith("data:image/")
    ):
        return data
    if isinstance(data, dict):
        for key in ("url", "image_url", "image"):
            val = data.get(key)
            if isinstance(val, str) and val.startswith(("http://", "https://", "data:image/")):
                return val
            if isinstance(val, dict):
                nested = extract_image_url_from_json(val)
                if nested:
                    return nested
        for key in ("images", "output", "data"):
            if key in data:
                nested = extract_image_url_from_json(data[key])
                if nested:
                    return nested
    if isinstance(data, list):
        for item in data:
            nested = extract_image_url_from_json(item)
            if nested:
                return nested
    return None


def result_from_response(response: httpx.Response, *, provider: str, prompt_used: str) -> ImageResult | None:
    """Parse binary image bytes or JSON image URL into ImageResult."""
    content_type = (response.headers.get("content-type") or "").lower()
    body = response.content
    if not body:
        return None

    if "application/json" in content_type or body[:1] in (b"{", b"["):
        try:
            data = response.json()
        except json.JSONDecodeError:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                return None
        url = extract_image_url_from_json(data)
        if url:
            return ImageResult(image_url=url, provider=provider, prompt_used=prompt_used)
        return None

    mime = "image/png"
    if "jpeg" in content_type or "jpg" in content_type:
        mime = "image/jpeg"
    elif "webp" in content_type:
        mime = "image/webp"
    elif not content_type.startswith("image/"):
        # Some gateways omit content-type; treat as PNG if payload looks binary.
        if body[:8].startswith(b"\x89PNG") or body[:2] == b"\xff\xd8":
            mime = "image/png" if body[:8].startswith(b"\x89PNG") else "image/jpeg"
        else:
            return None

    b64 = base64.b64encode(body).decode("ascii")
    return ImageResult(
        image_url=f"data:{mime};base64,{b64}",
        provider=provider,
        prompt_used=prompt_used,
    )


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
                "https://huggingface.co/settings/tokens (enable Inference Providers), "
                "set HF_API_TOKEN on Render (Environment), redeploy, then retry. "
                "Or switch to Pollinations (no key).",
                status_code=503,
            )

        used = truncate_image_prompt(prompt, max_len=1800)
        model = settings.hf_image_model.strip()
        w, h = _snap_dim(width), _snap_dim(height)

        # FLUX is served via Inference Providers (fal-ai), not classic hf-inference alone.
        urls = [
            f"https://router.huggingface.co/fal-ai/{model}",
            f"https://router.huggingface.co/hf-inference/models/{model}",
            f"https://api-inference.huggingface.co/models/{model}",
        ]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "*/*",
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
                except httpx.RequestError as exc:
                    last_error = (
                        "Could not reach Hugging Face inference API "
                        f"({type(exc).__name__}: {exc})."
                    )
                    continue

                if response.status_code == 401:
                    raise LLMProviderError(
                        "Hugging Face rejected the token. Check HF_API_TOKEN on Render and "
                        "that it has Inference Providers permission.",
                        401,
                    )
                if response.status_code == 429:
                    raise LLMProviderError(
                        "Hugging Face rate limit reached. Wait and retry, or use Pollinations.",
                        429,
                    )
                if response.status_code == 503:
                    try:
                        response = await client.post(url, headers=headers, json=payload)
                    except httpx.HTTPError as exc:
                        last_error = (
                            "Hugging Face model is loading. Retry in a few seconds "
                            f"({type(exc).__name__})."
                        )
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
                    continue

                parsed = result_from_response(
                    response, provider=self.name(), prompt_used=used
                )
                if parsed:
                    return parsed

                last_error = (
                    "Hugging Face returned an unreadable image payload "
                    f"(content-type={response.headers.get('content-type')!r})."
                )

        raise LLMProviderError(last_error, 502)
