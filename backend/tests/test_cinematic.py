import pytest

from app.api.schemas import EnhanceRequest
from app.models.domain import EnhanceMode, TargetType
from app.services.pipeline import EnhancementPipeline
from app.services.prompt_enhancement.cinematic_composer import (
    compose_cinematic,
    is_thin_or_meta_enhancement,
)


def test_composer_hanuman_preserves_story():
    result = compose_cinematic(
        "hanuman burning the lanka with teh tail on fire and lord sri rama is sensing his arrival at kiskindha kanda it should be real and not cartoonish",
        kind="video",
    )
    blob = (result.enhanced_prompt + "\n" + result.structured_prompt).lower()
    assert "hanuman" in blob
    assert "lanka" in blob
    assert "rama" in blob
    assert "camera" in result.structured_prompt.lower()
    assert "photoreal" in blob or "real" in blob
    assert "cartoon" in blob
    assert "provide a clear, complete response" not in blob


def test_thin_meta_detection():
    original = "hanuman burning lanka"
    thin = original + "\n\nProvide a clear, complete response. State assumptions explicitly if details are missing."
    assert is_thin_or_meta_enhancement(original, thin)


@pytest.mark.asyncio
async def test_pipeline_hanuman_dual_format(mock_provider):
    pipe = EnhancementPipeline(provider=mock_provider)
    resp = await pipe.run(
        EnhanceRequest(
            prompt=(
                "hanuman burning the lanka with teh tail on fire and lord sri rama "
                "is sensing his arrival at kiskindha kanda it should be real and not cartoonish"
            ),
            mode=EnhanceMode.ADVANCED,
            target=TargetType.VIDEO,
        )
    )
    assert resp.structured_prompt
    assert "Subject:" in resp.structured_prompt
    assert "Camera" in resp.structured_prompt
    lower = resp.enhanced_prompt.lower()
    assert "hanuman" in lower
    assert "lanka" in lower
    assert "provide a clear, complete response" not in lower
    assert resp.quality_after > resp.quality_before
