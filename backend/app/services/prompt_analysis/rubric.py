"""Deterministic category rubrics for prompt quality scoring."""

from __future__ import annotations

import re
from typing import Iterable

CATEGORY_DIMENSIONS: dict[str, list[str]] = {
    "image": [
        "subject",
        "composition",
        "environment",
        "lighting",
        "camera",
        "style",
        "color",
        "perspective",
        "realism",
        "negative",
    ],
    "video": [
        "subject",
        "action",
        "environment",
        "camera",
        "shot",
        "lighting",
        "atmosphere",
        "motion",
        "style",
        "duration",
    ],
    "coding": [
        "objective",
        "language",
        "framework",
        "input",
        "output",
        "constraints",
        "edge",
        "performance",
        "architecture",
        "test",
    ],
    "research": [
        "objective",
        "scope",
        "context",
        "timeframe",
        "sources",
        "format",
        "depth",
        "criteria",
    ],
    "general": [
        "goal",
        "audience",
        "tone",
        "format",
        "constraints",
        "context",
        "output",
    ],
}

# Keyword hints used to detect whether a dimension is present
DIMENSION_HINTS: dict[str, list[str]] = {
    "subject": ["subject", "of a", "showing", "featuring", "about"],
    "composition": ["composition", "framing", "rule of thirds", "centered", "wide shot"],
    "environment": ["environment", "city", "park", "room", "outdoor", "indoor", "street", "skyline"],
    "lighting": ["lighting", "neon", "sunlight", "volumetric", "soft light", "harsh", "golden hour"],
    "camera": ["camera", "tracking", "drone", "close-up", "wide-angle", "lens", "pan", "tilt"],
    "style": ["style", "cinematic", "photorealistic", "illustration", "minimal", "noir"],
    "color": ["color", "palette", "teal", "warm tones", "monochrome", "saturated"],
    "perspective": ["perspective", "first-person", "bird's-eye", "eye-level", "low angle"],
    "realism": ["photorealistic", "realistic", "believable", "grounded"],
    "negative": ["avoid", "no ", "without", "do not", "don't", "exclude"],
    "action": ["running", "flying", "moving", "walking", "detect", "create", "write", "build"],
    "shot": ["shot", "take", "scene", "sequence", "cut"],
    "atmosphere": ["atmosphere", "mood", "rain", "fog", "haze", "mist"],
    "motion": ["motion", "movement", "temporal", "smooth", "dynamic"],
    "duration": ["seconds", "duration", "15s", "30s", "minute"],
    "objective": ["create", "build", "implement", "write", "generate", "detect", "analyze"],
    "language": ["python", "typescript", "javascript", "java", "go", "rust", "sql"],
    "framework": ["fastapi", "flask", "django", "react", "express", "spring", "framework"],
    "input": ["input", "request", "accepts", "receives", "upload", "payload"],
    "output": ["output", "response", "return", "json", "schema", "format"],
    "constraints": ["must", "should", "constraint", "require", "limit", "only"],
    "edge": ["edge case", "error", "invalid", "empty", "timeout", "fail"],
    "performance": ["performance", "latency", "throughput", "scale", "memory"],
    "architecture": ["architecture", "modular", "layer", "service", "endpoint"],
    "test": ["test", "pytest", "unit test", "coverage", "checklist"],
    "scope": ["scope", "include", "exclude", "focus", "limit to"],
    "context": ["context", "background", "given that", "because"],
    "timeframe": ["202", "recent", "last year", "timeframe", "since"],
    "sources": ["sources", "citation", "peer-reviewed", "primary"],
    "format": ["format", "markdown", "bullet", "table", "structured", "email"],
    "depth": ["depth", "detailed", "comprehensive", "brief", "summary"],
    "criteria": ["criteria", "success", "evaluate", "quality", "acceptance"],
    "goal": ["goal", "want", "need", "please", "help me"],
    "audience": ["audience", "manager", "customer", "beginner", "executive"],
    "tone": ["tone", "professional", "polite", "casual", "formal"],
}


def _normalize_category(category: str) -> str:
    c = (category or "general").lower().strip()
    aliases = {
        "text": "general",
        "text_generation": "general",
        "marketing": "general",
        "business": "general",
        "education": "general",
        "automation": "general",
        "reasoning": "general",
        "summarization": "general",
        "image_generation": "image",
        "video_generation": "video",
        "code": "coding",
        "coding_model": "coding",
    }
    return aliases.get(c, c if c in CATEGORY_DIMENSIONS else "general")


def present_dimensions(prompt: str, category: str) -> list[str]:
    text = prompt.lower()
    dims = CATEGORY_DIMENSIONS[_normalize_category(category)]
    present: list[str] = []
    for dim in dims:
        hints = DIMENSION_HINTS.get(dim, [dim])
        if any(h in text for h in hints):
            present.append(dim)
    # Length / structure bonuses as weak signals
    if len(prompt.split()) >= 20 and "context" not in present and "context" in dims:
        if "," in prompt or "." in prompt:
            present.append("context")
    return present


def missing_dimensions(prompt: str, category: str) -> list[str]:
    cat = _normalize_category(category)
    dims = CATEGORY_DIMENSIONS[cat]
    present = set(present_dimensions(prompt, cat))
    return [d for d in dims if d not in present]


def score_prompt_quality(prompt: str, category: str) -> int:
    """
    Score 0–100 based on clarity, specificity, context, completeness,
    constraints, output definition, and ambiguity — not raw length.
    """
    cat = _normalize_category(category)
    dims = CATEGORY_DIMENSIONS[cat]
    present = present_dimensions(prompt, cat)
    coverage = len(present) / max(len(dims), 1)

    words = re.findall(r"\b\w+\b", prompt.lower())
    word_count = len(words)
    # Specificity: prefer concrete nouns/adjectives over empty adjectives alone
    fluff = {"stunning", "beautiful", "amazing", "incredible", "awesome", "nice", "great"}
    fluff_ratio = sum(1 for w in words if w in fluff) / max(word_count, 1)

    clarity = 0.35
    if word_count >= 5:
        clarity += 0.25
    if any(p in prompt.lower() for p in ("create", "write", "build", "generate", "make", "explain")):
        clarity += 0.2
    if prompt.strip().endswith((".", "?", "!")) or "\n" in prompt:
        clarity += 0.1
    clarity = min(1.0, clarity)

    specificity = min(1.0, coverage * 1.1) * (1.0 - min(0.4, fluff_ratio * 3))
    completeness = coverage
    constraints = 1.0 if any(k in prompt.lower() for k in ("must", "should", "do not", "don't", "avoid", "only", "require")) else 0.25
    output_def = 1.0 if any(k in prompt.lower() for k in ("format", "json", "return", "output", "response", "email", "markdown")) else 0.3
    ambiguity_penalty = 0.0
    if word_count < 8:
        ambiguity_penalty += 0.25
    if prompt.lower().count("thing") + prompt.lower().count("stuff") > 0:
        ambiguity_penalty += 0.15

    score = (
        clarity * 18
        + specificity * 22
        + completeness * 22
        + constraints * 12
        + output_def * 14
        + (1.0 - ambiguity_penalty) * 12
    )
    # Mild length signal: too short hurts; very long without coverage doesn't help much
    if word_count < 6:
        score *= 0.75
    elif word_count > 40 and coverage < 0.4:
        score *= 0.9

    return max(0, min(100, int(round(score))))


def material_gaps_for_category(prompt: str, category: str, max_gaps: int = 6) -> list[str]:
    """Return only high-value missing dimensions for the category."""
    missing = missing_dimensions(prompt, category)
    priority = {
        "video": ["subject", "action", "environment", "camera", "atmosphere", "style", "lighting", "motion"],
        "image": ["subject", "environment", "lighting", "camera", "style", "composition"],
        "coding": ["objective", "language", "input", "output", "constraints", "edge", "test"],
        "research": ["objective", "scope", "sources", "format", "criteria"],
        "general": ["goal", "audience", "tone", "format", "constraints", "output"],
    }
    cat = _normalize_category(category)
    order = priority.get(cat, missing)
    ordered = [d for d in order if d in missing] + [d for d in missing if d not in order]
    return ordered[:max_gaps]


def map_target_to_category(target: str) -> str:
    t = (target or "general").lower()
    mapping = {
        "image": "image",
        "video": "video",
        "coding": "coding",
        "research": "research",
        "general": "general",
        "chatgpt": "general",
        "claude": "general",
        "gemini": "general",
        "custom": "general",
    }
    return mapping.get(t, "general")
