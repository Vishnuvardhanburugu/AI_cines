"""Enhance stage: context-aware prompt improvement."""

from __future__ import annotations

import json

from app.models.domain import (
    AnalyzeResult,
    EnhanceMode,
    EnhanceOperation,
    EnhanceResult,
    TargetType,
)
from app.providers.base import LLMProvider
from app.services.prompt_analysis.rubric import map_target_to_category, score_prompt_quality
from app.services.prompt_enhancement.cinematic_composer import (
    compose_cinematic,
    is_thin_or_meta_enhancement,
)
from app.services.prompt_enhancement.targets.packs import get_target_pack

ENHANCE_SYSTEM = """You are a semantic prompt enhancer that produces MASTER PROMPTS.
Preserve intent. Improve specificity with material detail — especially for video/image.

Never:
- Append meta boilerplate like "Provide a clear, complete response" or "state assumptions explicitly"
- Replace simple words with fancier synonyms without adding useful information
- Invent unrelated plot, characters, frameworks, dates, or facts
- Expose chain-of-thought

Always:
- Keep subject, objective, constraints, tone, and required output
- For video/image: produce a cinematic production-ready master prompt
- Mark creative (non-implied) fills in assumptions[]
- Prefer clarification_questions for high-impact unknowns
- For coding: do not arbitrarily choose FastAPI, YOLO, Postgres, Docker, etc.
- For leave/email: do not invent dates or reasons; use placeholders

Return JSON only with keys:
enhanced_prompt (flowing ready-to-paste paragraph OR polished instruction),
structured_prompt (labeled sections string OR null for non-visual tasks),
changes (array), assumptions (array), explanation (1-2 sentences),
clarification_questions (array).

For video/image structured_prompt MUST use these labels on separate lines:
Subject:
Action:
Setting:
Camera / Shot:
Lighting:
Atmosphere:
Motion / Continuity:
Style / Realism:
Negatives / Constraints:
"""


def _mode_instructions(mode: EnhanceMode) -> str:
    if mode == EnhanceMode.MINIMAL:
        return (
            "MODE=minimal: Preserve the user's wording as much as possible. "
            "Fix clarity and light structure only. Almost no new details."
        )
    if mode == EnhanceMode.ADVANCED:
        return (
            "MODE=advanced: Produce a full cinematic/master restructure for the target. "
            "Add material camera, lighting, atmosphere, motion, and style detail while "
            "preserving characters and story beat. List creative assumptions."
        )
    return (
        "MODE=balanced: Improve clarity, specificity, structure, and useful missing information. "
        "For video/image, include cinematic parameters. Mark creative fills as assumptions."
    )


def _operations_instructions(operations: list[EnhanceOperation]) -> str:
    if not operations:
        return "No extra operations."
    mapping = {
        EnhanceOperation.MORE_SPECIFIC: "Make the prompt more specific where material.",
        EnhanceOperation.CONCISE: "Prefer a concise enhanced prompt; remove fluff.",
        EnhanceOperation.CREATIVE: "Allow more creative (but listed) assumptions.",
        EnhanceOperation.PROFESSIONAL: "Use a professional tone and structure.",
        EnhanceOperation.ADD_CONSTRAINTS: "Add sensible constraints and acceptance criteria.",
        EnhanceOperation.OPTIMIZE_IMAGE: "Bias enhancement toward image-generation parameters.",
        EnhanceOperation.OPTIMIZE_VIDEO: "Bias enhancement toward video-generation cinematic master prompts.",
        EnhanceOperation.OPTIMIZE_CODING: "Bias enhancement toward coding-task completeness.",
    }
    lines = [mapping[op] for op in operations if op in mapping]
    return "EXTRA OPERATIONS:\n- " + "\n- ".join(lines) if lines else "No extra operations."


def _is_visual_target(target: TargetType, category: str) -> bool:
    if target in (TargetType.VIDEO, TargetType.IMAGE):
        return True
    cat = (category or "").lower()
    return cat in {"video", "image", "video_generation", "image_generation"}


async def enhance_prompt(
    provider: LLMProvider,
    prompt: str,
    analysis: AnalyzeResult,
    mode: EnhanceMode,
    target: TargetType,
    operations: list[EnhanceOperation] | None = None,
    validation_issues: list[str] | None = None,
    force_minimal: bool = False,
) -> EnhanceResult:
    effective_mode = EnhanceMode.MINIMAL if force_minimal else mode
    operations = operations or []

    effective_target = target
    if EnhanceOperation.OPTIMIZE_IMAGE in operations:
        effective_target = TargetType.IMAGE
    elif EnhanceOperation.OPTIMIZE_VIDEO in operations:
        effective_target = TargetType.VIDEO
    elif EnhanceOperation.OPTIMIZE_CODING in operations:
        effective_target = TargetType.CODING

    pack = get_target_pack(effective_target)
    intent_payload = analysis.intent.model_dump()
    visual = _is_visual_target(effective_target, analysis.category)

    retry_block = ""
    if validation_issues:
        retry_block = (
            "\nPREVIOUS ENHANCEMENT FAILED VALIDATION. Fix these issues:\n- "
            + "\n- ".join(validation_issues)
            + "\nSimplify if needed. Do not add unsupported major assumptions.\n"
        )

    dual_hint = ""
    if visual and effective_mode != EnhanceMode.MINIMAL:
        dual_hint = (
            "\nVISUAL MASTER PROMPT REQUIRED:\n"
            "- structured_prompt = labeled production sections\n"
            "- enhanced_prompt = one flowing cinematic paragraph ready to paste into a video/image model\n"
            "- Do NOT return meta-instructions about responding clearly\n"
        )

    user_msg = f"""{_mode_instructions(effective_mode)}

TARGET PACK:
{pack}
{dual_hint}
{_operations_instructions(operations)}

CATEGORY: {analysis.category}
QUALITY_BEFORE: {analysis.quality_before}
MATERIAL_GAPS: {json.dumps(analysis.material_gaps)}
INTENT_METADATA: {json.dumps(intent_payload)}
ANALYSIS: {analysis.analysis_summary}
{retry_block}
ORIGINAL PROMPT:
{prompt}

MODE: {effective_mode.value}
TARGET: {effective_target.value}

Produce the enhanced prompt JSON now.
"""

    data = await provider.complete_json(ENHANCE_SYSTEM, user_msg, temperature=0.4)
    enhanced = str(data.get("enhanced_prompt") or "").strip()
    structured = data.get("structured_prompt")
    structured_str = str(structured).strip() if structured else None

    # Guardrail: replace thin/meta visual output with cinematic composer
    if visual and effective_mode != EnhanceMode.MINIMAL and is_thin_or_meta_enhancement(prompt, enhanced):
        kind = "image" if effective_target == TargetType.IMAGE else "video"
        composed = compose_cinematic(prompt, kind=kind)
        enhanced = composed.enhanced_prompt
        structured_str = composed.structured_prompt
        data = {
            "changes": composed.changes,
            "assumptions": composed.assumptions,
            "explanation": composed.explanation,
            "clarification_questions": composed.clarification_questions,
        }
    elif visual and effective_mode != EnhanceMode.MINIMAL and not structured_str:
        kind = "image" if effective_target == TargetType.IMAGE else "video"
        composed = compose_cinematic(prompt, kind=kind)
        structured_str = composed.structured_prompt
        if not enhanced:
            enhanced = composed.enhanced_prompt

    if not enhanced:
        enhanced = prompt

    rubric_cat = map_target_to_category(
        effective_target.value if effective_target != TargetType.GENERAL else analysis.category
    )
    quality_after = score_prompt_quality(
        f"{enhanced}\n{structured_str or ''}", rubric_cat
    )

    return EnhanceResult(
        enhanced_prompt=enhanced,
        structured_prompt=structured_str,
        changes=_as_str_list(data.get("changes")),
        assumptions=_as_str_list(data.get("assumptions")),
        explanation=str(data.get("explanation") or ""),
        clarification_questions=_as_str_list(data.get("clarification_questions")),
        quality_after=quality_after,
    )


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]
