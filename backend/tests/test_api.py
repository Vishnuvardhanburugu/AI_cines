import os

os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_enhance_success():
    r = client.post(
        "/api/enhance",
        json={
            "prompt": "Make a video of a futuristic city.",
            "mode": "balanced",
            "target": "video",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["original_prompt"]
    assert data["enhanced_prompt"]
    assert "quality_before" in data
    assert "quality_after" in data
    assert isinstance(data["changes"], list)


def test_empty_prompt_rejected():
    r = client.post("/api/enhance", json={"prompt": "   ", "mode": "balanced", "target": "general"})
    assert r.status_code == 400


def test_invalid_mode_rejected():
    r = client.post(
        "/api/enhance",
        json={"prompt": "hello", "mode": "ultra", "target": "general"},
    )
    assert r.status_code == 422


def test_oversized_prompt_rejected():
    r = client.post(
        "/api/enhance",
        json={"prompt": "x" * 13000, "mode": "balanced", "target": "general"},
    )
    assert r.status_code in (400, 422)
