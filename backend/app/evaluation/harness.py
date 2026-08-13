"""Evaluation harness for intent preservation / hallucination / specificity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.prompt_analysis.rubric import score_prompt_quality

DATASET_PATH = Path(__file__).with_name("dataset.json")


def load_dataset(path: Path | None = None) -> list[dict[str, Any]]:
    p = path or DATASET_PATH
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def score_case(
    case: dict[str, Any],
    enhanced_prompt: str,
    *,
    category: str | None = None,
) -> dict[str, Any]:
    original = case["input"]
    must_preserve = case.get("must_preserve", [])
    must_not_invent = case.get("must_not_invent", [])
    cat = category or case.get("expected_category", "general")

    enhanced_l = enhanced_prompt.lower()
    preserved = [t for t in must_preserve if t.lower() in enhanced_l]
    invent_hits = [t for t in must_not_invent if t.lower() in enhanced_l and t.lower() not in original.lower()]

    intent_preservation = len(preserved) / max(len(must_preserve), 1)
    hallucination = len(invent_hits) / max(len(must_not_invent), 1)
    # Relevance: quality delta positive and not pure fluff expansion
    before = score_prompt_quality(original, cat)
    after = score_prompt_quality(enhanced_prompt, cat)
    specificity = after / 100.0
    meaningful = 1.0 if after >= before + 5 or after >= 70 else (0.5 if after >= before else 0.0)
    # Penalize hallucination in overall
    overall = (
        intent_preservation * 0.4
        + (1.0 - hallucination) * 0.3
        + specificity * 0.15
        + meaningful * 0.15
    )

    return {
        "id": case.get("id"),
        "quality_before": before,
        "quality_after": after,
        "intent_preservation": round(intent_preservation, 3),
        "specificity": round(specificity, 3),
        "relevance": round(meaningful, 3),
        "hallucination": round(hallucination, 3),
        "overall": round(overall, 3),
        "preserved": preserved,
        "invent_hits": invent_hits,
    }
