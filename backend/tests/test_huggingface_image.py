import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("IMAGE_PROVIDER", "mock")

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.huggingface_image import (
    HuggingFaceImageProvider,
    extract_image_url_from_json,
    result_from_response,
)
from app.api.schemas import GenerateImageRequest
from app.services import image_generation as image_gen_mod


def test_extract_image_url_from_nested_json():
    data = {"images": [{"url": "https://cdn.example.com/a.png"}]}
    assert extract_image_url_from_json(data) == "https://cdn.example.com/a.png"


def test_extract_image_url_from_data_uri():
    data = {"image": "data:image/png;base64,abc"}
    assert extract_image_url_from_json(data) == "data:image/png;base64,abc"


def test_result_from_response_json_url():
    response = httpx.Response(
        200,
        headers={"content-type": "application/json"},
        json={"images": [{"url": "https://cdn.example.com/flux.png"}]},
    )
    result = result_from_response(response, provider="huggingface", prompt_used="test")
    assert result is not None
    assert result.image_url == "https://cdn.example.com/flux.png"
    assert result.provider == "huggingface"


def test_result_from_response_png_bytes():
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    response = httpx.Response(
        200,
        headers={"content-type": "image/png"},
        content=png,
    )
    result = result_from_response(response, provider="huggingface", prompt_used="test")
    assert result is not None
    assert result.image_url.startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_hf_missing_token_503():
    os.environ["HF_API_TOKEN"] = ""
    get_settings.cache_clear()
    with pytest.raises(LLMProviderError) as exc:
        await HuggingFaceImageProvider().generate("a cliff still", width=768, height=1344)
    assert exc.value.status_code == 503
    assert "HF_API_TOKEN" in exc.value.message


@pytest.mark.asyncio
async def test_generate_image_hf_falls_back_to_pollinations():
    os.environ["HF_API_TOKEN"] = "hf_test_token"
    get_settings.cache_clear()

    failing = AsyncMock(
        side_effect=LLMProviderError("Could not reach Hugging Face", 502)
    )
    poll_result = MagicMock(
        image_url="https://image.pollinations.ai/prompt/test",
        provider="pollinations",
        prompt_used="packed",
    )

    with (
        patch(
            "app.services.image_generation.get_image_provider",
            return_value=MagicMock(generate=failing),
        ),
        patch(
            "app.services.image_generation.PollinationsImageProvider"
        ) as PollCls,
    ):
        PollCls.return_value.generate = AsyncMock(return_value=poll_result)
        out = await image_gen_mod.generate_image(
            GenerateImageRequest(
                prompt="Hanuman on a cliff over burning Lanka",
                provider="huggingface",
                aspect="portrait",
            )
        )

    assert out.provider == "pollinations"
    assert "pollinations" in out.image_url
