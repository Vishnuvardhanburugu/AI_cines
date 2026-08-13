import os

os.environ["IMAGE_PROVIDER"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.providers.pollinations_image import PollinationsImageProvider
from app.main import app

get_settings.cache_clear()

client = TestClient(app)


def test_pollinations_url_encodes_prompt():
    provider = PollinationsImageProvider()
    url = provider.build_url("hanuman burning lanka", width=768, height=1344)
    assert "image.pollinations.ai/prompt/" in url
    assert "width=768" in url
    assert "height=1344" in url


def test_generate_image_mock_api():
    get_settings.cache_clear()
    r = client.post(
        "/api/generate-image",
        json={
            "prompt": "photoreal cinematic Hanuman on a cliff over burning Lanka",
            "width": 768,
            "height": 1344,
            "provider": "mock",
            "aspect": "portrait",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "mock"
    assert data["image_url"].startswith("data:image/")
    assert "depict the core action" not in data["prompt_used"].lower()


def test_generate_image_gemini_without_key_503():
    get_settings.cache_clear()
    r = client.post(
        "/api/generate-image",
        json={
            "prompt": "Hanuman overlooking burning Lanka",
            "provider": "gemini",
            "aspect": "portrait",
        },
    )
    assert r.status_code == 503
    assert "GEMINI_API_KEY" in r.json()["detail"]


def test_generate_image_empty_rejected():
    r = client.post("/api/generate-image", json={"prompt": "   "})
    assert r.status_code == 400
