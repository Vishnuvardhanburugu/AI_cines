"""Optional live evaluation against a real LLM provider.

Usage:
  LLM_PROVIDER=openai OPENAI_API_KEY=... python -m app.evaluation.run_live
"""

from __future__ import annotations

import asyncio
import json
import sys

from app.api.schemas import EnhanceRequest
from app.evaluation.harness import load_dataset, score_case
from app.models.domain import EnhanceMode, TargetType
from app.services.pipeline import EnhancementPipeline


async def main() -> int:
    dataset = load_dataset()
    pipe = EnhancementPipeline()
    results = []

    target_map = {
        "video": TargetType.VIDEO,
        "image": TargetType.IMAGE,
        "coding": TargetType.CODING,
        "research": TargetType.RESEARCH,
        "general": TargetType.GENERAL,
    }

    for case in dataset:
        target = target_map.get(case.get("expected_category", "general"), TargetType.GENERAL)
        resp = await pipe.run(
            EnhanceRequest(
                prompt=case["input"],
                mode=EnhanceMode.BALANCED,
                target=target,
            )
        )
        scored = score_case(case, resp.enhanced_prompt, category=resp.category)
        scored["enhanced_prompt"] = resp.enhanced_prompt
        results.append(scored)
        print(f"{scored['id']}: overall={scored['overall']} intent={scored['intent_preservation']} hall={scored['hallucination']}")

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
