import pytest

from app.api.schemas import EnhanceRequest
from app.models.domain import EnhanceMode, TargetType
from app.services.pipeline import EnhancementPipeline


@pytest.mark.asyncio
async def test_video_enhancement_preserves_intent(mock_provider):
    pipe = EnhancementPipeline(provider=mock_provider)
    resp = await pipe.run(
        EnhanceRequest(
            prompt="Make a video of a futuristic city.",
            mode=EnhanceMode.BALANCED,
            target=TargetType.VIDEO,
        )
    )
    assert "futuristic" in resp.enhanced_prompt.lower()
    assert "city" in resp.enhanced_prompt.lower()
    assert resp.quality_after >= resp.quality_before
    assert resp.changes
    assert resp.explanation


@pytest.mark.asyncio
async def test_coding_does_not_invent_stack(mock_provider):
    pipe = EnhancementPipeline(provider=mock_provider)
    resp = await pipe.run(
        EnhanceRequest(
            prompt="Create a Python API that receives an image and detects objects.",
            mode=EnhanceMode.BALANCED,
            target=TargetType.CODING,
        )
    )
    lower = resp.enhanced_prompt.lower()
    assert "python" in lower
    assert "fastapi" not in lower
    assert "yolo" not in lower
    assert "postgresql" not in lower


@pytest.mark.asyncio
async def test_email_does_not_invent_dates(mock_provider):
    pipe = EnhancementPipeline(provider=mock_provider)
    resp = await pipe.run(
        EnhanceRequest(
            prompt="Write an email asking my manager for leave.",
            mode=EnhanceMode.BALANCED,
            target=TargetType.GENERAL,
        )
    )
    assert "january" not in resp.enhanced_prompt.lower()
    assert "manager" in resp.enhanced_prompt.lower()
    assert "leave" in resp.enhanced_prompt.lower()


@pytest.mark.asyncio
async def test_minimal_mode_stays_close(mock_provider):
    pipe = EnhancementPipeline(provider=mock_provider)
    original = "Make a video of a futuristic city."
    resp = await pipe.run(
        EnhanceRequest(
            prompt=original,
            mode=EnhanceMode.MINIMAL,
            target=TargetType.VIDEO,
        )
    )
    # Mock minimal mostly keeps original
    assert "futuristic city" in resp.enhanced_prompt.lower()
