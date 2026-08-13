"""Analyze stage: classification, intent extraction, gaps, quality."""

from __future__ import annotations

from app.models.domain import AnalyzeResult, IntentModel, TargetType
from app.providers.base import LLMProvider
from app.services.prompt_analysis.rubric import (
    map_target_to_category,
    material_gaps_for_category,
    score_prompt_quality,
)

ANALYZE_SYSTEM = """You are a prompt analysis engine for a semantic prompt enhancer.
Extract structured metadata from the user's prompt. Do NOT rewrite the prompt.
Do NOT include chain-of-thought or hidden reasoning. Return JSON only with these keys:
category, goal, subject, action, context, constraints (array), desired_output, style,
audience, known_details (array), missing_details (array), ambiguities (array),
material_gaps (array of gaps that materially matter for this task), analysis_summary (one short sentence).

Rules:
- Preserve the user's intent exactly in the extracted fields.
- material_gaps: only dimensions that would meaningfully improve the prompt for the task.
- Do not invent facts the user did not imply.
- category should be one of: text_generation, image, video, coding, data_analysis,
  summarization, research, reasoning, marketing, business, education, automation,
  general_assistant, other.
"""


async def analyze_prompt(
    provider: LLMProvider,
    prompt: str,
    target: TargetType,
) -> AnalyzeResult:
    user_msg = (
        f"TARGET HINT: {target.value}\n\n"
        f"ORIGINAL PROMPT:\n{prompt}\n\n"
        "Perform intent extraction and gap analysis. Return JSON only."
    )

    try:
        data = await provider.complete_json(ANALYZE_SYSTEM, user_msg, temperature=0.1)
    except Exception:
        # Keyword fallback when provider fails mid-pipeline is handled upstream;
        # here we still allow a local heuristic path for mock-less offline use.
        data = _heuristic_analyze(prompt, target)

    category = str(data.get("category") or map_target_to_category(target.value))
    # Prefer explicit user target for visual/coding when selected
    if target in (TargetType.IMAGE, TargetType.VIDEO, TargetType.CODING, TargetType.RESEARCH):
        category = target.value

    intent = IntentModel(
        goal=str(data.get("goal") or ""),
        subject=str(data.get("subject") or ""),
        action=str(data.get("action") or ""),
        context=str(data.get("context") or ""),
        constraints=_as_str_list(data.get("constraints")),
        desired_output=str(data.get("desired_output") or ""),
        style=str(data.get("style") or ""),
        audience=str(data.get("audience") or ""),
        known_details=_as_str_list(data.get("known_details")),
        missing_details=_as_str_list(data.get("missing_details")),
        ambiguities=_as_str_list(data.get("ambiguities")),
    )

    rubric_category = map_target_to_category(
        target.value if target != TargetType.GENERAL else category
    )
    gaps = _as_str_list(data.get("material_gaps")) or material_gaps_for_category(
        prompt, rubric_category
    )
    quality = score_prompt_quality(prompt, rubric_category)

    return AnalyzeResult(
        category=category,
        intent=intent,
        material_gaps=gaps,
        quality_before=quality,
        analysis_summary=str(data.get("analysis_summary") or ""),
    )


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def _heuristic_analyze(prompt: str, target: TargetType) -> dict:
    lower = prompt.lower()
    category = map_target_to_category(target.value)
    if target == TargetType.GENERAL:
        if any(w in lower for w in ("video", "cinematic", "clip")):
            category = "video"
        elif any(w in lower for w in ("image", "photo", "illustration")):
            category = "image"
        elif any(w in lower for w in ("python", "api", "code", "function")):
            category = "coding"
        elif "research" in lower:
            category = "research"

    gaps = material_gaps_for_category(prompt, category)
    return {
        "category": category,
        "goal": "Complete the user's request",
        "subject": prompt[:100],
        "action": "",
        "context": "",
        "constraints": [],
        "desired_output": "",
        "style": "",
        "audience": "",
        "known_details": [prompt[:200]],
        "missing_details": gaps,
        "ambiguities": ["underspecified"] if len(prompt.split()) < 12 else [],
        "material_gaps": gaps,
        "analysis_summary": "Heuristic analysis used due to provider unavailability.",
    }
