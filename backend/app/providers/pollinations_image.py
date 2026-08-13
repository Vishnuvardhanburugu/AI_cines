"""Free Pollinations text-to-image provider (no API key required)."""

from __future__ import annotations

from urllib.parse import quote

from app.core.config import get_settings
from app.providers.image_base import ImageProvider, ImageResult, truncate_image_prompt


class PollinationsImageProvider(ImageProvider):
    def name(self) -> str:
        return "pollinations"

    def build_url(self, prompt: str, *, width: int = 1024, height: int = 576) -> str:
        settings = get_settings()
        used = truncate_image_prompt(prompt)
        base = settings.pollinations_base_url.rstrip("/")
        encoded = quote(used, safe="")
        # nologo=true is best-effort; anonymous may still watermark
        return (
            f"{base}/prompt/{encoded}"
            f"?width={width}&height={height}&nologo=true&model=flux"
        )

    async def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 576,
    ) -> ImageResult:
        used = truncate_image_prompt(prompt)
        url = self.build_url(used, width=width, height=height)
        return ImageResult(image_url=url, provider=self.name(), prompt_used=used)
