"""Deterministic placeholder image for tests / offline demos."""

from __future__ import annotations

import base64
from urllib.parse import quote

from app.providers.image_base import ImageProvider, ImageResult, truncate_image_prompt


class MockImageProvider(ImageProvider):
    def name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 576,
    ) -> ImageResult:
        used = truncate_image_prompt(prompt)
        label = quote(used[:40] or "mock")
        # Minimal SVG data URL — no network
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<rect width="100%" height="100%" fill="#0f766e"/>'
            f'<text x="50%" y="45%" fill="#fffdf8" font-size="28" text-anchor="middle" '
            f'font-family="Georgia, serif">AICines Mock Image</text>'
            f'<text x="50%" y="58%" fill="#ccfbf1" font-size="14" text-anchor="middle" '
            f'font-family="sans-serif">{label}</text>'
            f"</svg>"
        )
        b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return ImageResult(
            image_url=f"data:image/svg+xml;base64,{b64}",
            provider=self.name(),
            prompt_used=used,
        )
