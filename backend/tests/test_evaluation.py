import pytest

from app.api.schemas import EnhanceRequest
from app.evaluation.harness import load_dataset, score_case
from app.models.domain import EnhanceMode, TargetType
from app.services.pipeline import EnhancementPipeline


@pytest.mark.asyncio
async def test_dataset_mock_eval_targets(mock_provider):
    dataset = load_dataset()
    pipe = EnhancementPipeline(provider=mock_provider)
    results = []

    for case in dataset:
        target_map = {
            "video": TargetType.VIDEO,
            "image": TargetType.IMAGE,
            "coding": TargetType.CODING,
            "research": TargetType.RESEARCH,
            "general": TargetType.GENERAL,
        }
        target = target_map.get(case.get("expected_category", "general"), TargetType.GENERAL)
        resp = await pipe.run(
            EnhanceRequest(
                prompt=case["input"],
                mode=EnhanceMode.BALANCED,
                target=target,
            )
        )
        scored = score_case(case, resp.enhanced_prompt, category=resp.category)
        results.append(scored)
        assert scored["intent_preservation"] >= 0.95, case["id"]
        assert scored["hallucination"] == 0.0, f"{case['id']} invented {scored['invent_hits']}"

    assert results
