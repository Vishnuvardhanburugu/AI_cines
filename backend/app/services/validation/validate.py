"""LLM validation stage (Layer B) + orchestration with rule guards."""

from __future__ import annotations

import json

from app.models.domain import AnalyzeResult, EnhanceResult, ValidationResult
from app.providers.base import LLMProvider
from app.services.validation.guards import run_rule_guards

VALIDATE_SYSTEM = """You are a strict prompt-enhancement validator.
Return JSON only with keys: pass (boolean), issues (array of short strings),
unsupported_assumptions (array of short strings).

Check:
1) Did the enhancement preserve original intent?
2) Did it introduce unsupported major assumptions (not listed or not implied)?
3) Did it contradict the user?
4) Did it unnecessarily inflate length without specificity?
5) Did it actually improve specificity for the task?
6) Are added details relevant?
7) Is the output appropriate for the target task?

Do not rewrite the prompt. Do not include chain-of-thought.
"""


async def validate_enhancement(
    provider: LLMProvider,
    original: str,
    enhance: EnhanceResult,
    analysis: AnalyzeResult,
    *,
    use_llm: bool = True,
) -> ValidationResult:
    rule_result = run_rule_guards(
        original, enhance, analysis, analysis.quality_before
    )

    if not use_llm:
        return rule_result

    user_msg = f"""ORIGINAL:
{original}

ENHANCED:
{enhance.enhanced_prompt}

CATEGORY: {analysis.category}
LISTED_ASSUMPTIONS: {json.dumps(enhance.assumptions)}
CHANGES: {json.dumps(enhance.changes)}

Validate the enhancement. Return JSON only.
"""

    try:
        data = await provider.complete_json(VALIDATE_SYSTEM, user_msg, temperature=0.0)
    except Exception:
        # If validator LLM fails, rely on deterministic guards
        return rule_result

    llm_pass = bool(data.get("pass", True))
    llm_issues = _as_str_list(data.get("issues"))
    llm_unsupported = _as_str_list(data.get("unsupported_assumptions"))

    combined_issues = list(dict.fromkeys(rule_result.issues + llm_issues))
    combined_unsupported = list(
        dict.fromkeys(rule_result.unsupported_assumptions + llm_unsupported)
    )
    passed = rule_result.passed and llm_pass and not combined_issues

    return ValidationResult(
        passed=passed,
        issues=combined_issues,
        unsupported_assumptions=combined_unsupported,
        should_degrade=rule_result.should_degrade or (not passed and len(combined_issues) >= 3),
    )


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]
