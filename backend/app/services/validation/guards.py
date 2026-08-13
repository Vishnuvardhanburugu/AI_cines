"""Deterministic validation guards (Layer A)."""

from __future__ import annotations

import re

from app.models.domain import AnalyzeResult, EnhanceResult, ValidationResult


def run_rule_guards(
    original: str,
    enhance: EnhanceResult,
    analysis: AnalyzeResult,
    quality_before: int,
) -> ValidationResult:
    issues: list[str] = []
    unsupported: list[str] = []

    enhanced = enhance.enhanced_prompt or ""
    if not enhanced.strip():
        return ValidationResult(
            passed=False,
            issues=["Enhanced prompt is empty."],
            should_degrade=True,
        )

    # Preserve distinctive tokens / short constraints (not full-sentence known_details)
    must_keep = _concrete_phrases(analysis.intent.constraints)
    must_keep.extend(_salient_tokens(original))
    must_keep = list(dict.fromkeys(must_keep))  # dedupe

    enhanced_lower = enhanced.lower()
    missing_keep = [p for p in must_keep if p.lower() not in enhanced_lower]
    # Tolerate some loss; fail if many concrete tokens disappear
    if must_keep and len(missing_keep) / max(len(must_keep), 1) > 0.6:
        issues.append(
            "Enhanced prompt appears to drop important user-specified details: "
            + ", ".join(missing_keep[:5])
        )

    # Anti-padding: much longer with small quality gain
    orig_len = max(len(original.split()), 1)
    enh_len = len(enhanced.split())
    quality_gain = enhance.quality_after - quality_before
    if enh_len > orig_len * 4 and quality_gain < 8:
        issues.append("Enhanced prompt is much longer without meaningful quality gain.")

    # Simple contradiction checks
    issues.extend(_contradiction_issues(original, enhanced))

    # Hallucinated stack choices for coding when user didn't mention them
    if _looks_coding(analysis.category, original):
        invented = _invented_stack_terms(original, enhanced)
        for term in invented:
            unsupported.append(f"Introduced '{term}' without user request")
            # Only hard-fail if assumption list doesn't mention it
            if not any(term.lower() in a.lower() for a in enhance.assumptions):
                issues.append(
                    f"Introduced specific technology '{term}' without listing it as an assumption."
                )

    # Leave/email: inventing dates
    if _looks_leave_email(original):
        if _has_invented_date(original, enhanced):
            issues.append("Invented specific dates that the user did not provide.")
            unsupported.append("Invented leave dates")

    passed = len(issues) == 0
    return ValidationResult(
        passed=passed,
        issues=issues,
        unsupported_assumptions=unsupported,
        should_degrade=not passed and quality_gain < 0,
    )


_STOP = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "with", "my",
    "your", "is", "are", "be", "this", "that", "it", "as", "at", "by", "from",
    "make", "create", "write", "generate", "please", "help", "me", "i", "we",
}


def _salient_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_+#.-]{3,}", text)
    out = []
    for t in tokens:
        if t.lower() in _STOP:
            continue
        # Prefer proper-ish or technical tokens
        if t[0].isupper() or t.lower() in {
            "python", "api", "video", "image", "email", "manager", "leave",
            "futuristic", "city", "object", "detect", "objects",
        }:
            out.append(t)
    return out[:12]


def _concrete_phrases(items: list[str]) -> list[str]:
    out = []
    for item in items:
        item = item.strip()
        if not item or len(item) < 3:
            continue
        # Skip long freeform sentences
        if len(item.split()) > 8:
            continue
        out.append(item)
    return out


def _contradiction_issues(original: str, enhanced: str) -> list[str]:
    issues = []
    o = original.lower()
    e = enhanced.lower()

    lang_pairs = [
        ("python", ["java", "javascript", "typescript", "golang", "ruby"]),
        ("javascript", ["python", "java", "golang"]),
        ("typescript", ["python", "java", "golang"]),
    ]
    for lang, others in lang_pairs:
        if lang in o and any(x in e and x not in o for x in others):
            # Allow mentioning comparisons; fail if primary language replaced
            if lang not in e:
                issues.append(f"Contradicts requested language '{lang}'.")

    if "no music" in o and "music" in e and "no music" not in e:
        issues.append("Contradicts 'no music' constraint.")
    if "without dialogue" in o and "dialogue" in e and "without dialogue" not in e:
        issues.append("Contradicts 'without dialogue' constraint.")
    return issues


def _looks_coding(category: str, original: str) -> bool:
    if category in {"coding", "code"}:
        return True
    lower = original.lower()
    return any(w in lower for w in ("python", "api", "function", "typescript", "code"))


def _invented_stack_terms(original: str, enhanced: str) -> list[str]:
    terms = [
        "fastapi", "flask", "django", "yolo", "postgresql", "postgres", "docker",
        "kubernetes", "redis", "mongodb", "tensorflow", "pytorch", "express",
    ]
    o = original.lower()
    e = enhanced.lower()
    return [t for t in terms if t in e and t not in o]


def _looks_leave_email(original: str) -> bool:
    lower = original.lower()
    return "email" in lower and ("leave" in lower or "manager" in lower)


def _has_invented_date(original: str, enhanced: str) -> bool:
    date_pat = re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
        r"(?:january|february|march|april|may|june|july|august|september|october|november|december)"
        r"\s+\d{1,2})\b",
        re.I,
    )
    orig_dates = set(m.group(0).lower() for m in date_pat.finditer(original))
    enh_dates = set(m.group(0).lower() for m in date_pat.finditer(enhanced))
    invented = enh_dates - orig_dates
    # Placeholders like [start date] are fine
    return bool(invented)
