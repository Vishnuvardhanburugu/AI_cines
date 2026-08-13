"""Target-aware instruction packs. Only claim what we actually encode."""

from __future__ import annotations

from app.models.domain import TargetType

PACKS: dict[str, str] = {
    "general": (
        "Optimize for a general-purpose LLM assistant. Prefer clear goals, constraints, "
        "audience, tone, and output format when useful."
    ),
    "image": (
        "Optimize for image generation as a CINEMATIC MASTER PROMPT. Require subject, action, "
        "setting, camera/composition, lighting, atmosphere, style/realism, and negatives. "
        "Return both labeled sections and a flowing paragraph. Do not invent unrelated subjects. "
        "Never append chatbot meta-instructions."
    ),
    "video": (
        "Optimize for video generation as a CINEMATIC MASTER PROMPT. Require subject, action, "
        "setting, camera movement, shot type, lighting, atmosphere, motion/continuity, "
        "style/realism, and negatives. Return both labeled sections and a flowing paragraph "
        "ready for video models. Preserve the user's story beat; do not invent an entire new plot. "
        "Never append chatbot meta-instructions."
    ),
    "coding": (
        "Optimize for coding assistants. Prefer objective, language, I/O, constraints, edge cases, "
        "expected behavior, and tests. Do NOT lock to a specific framework, library, model, "
        "or database unless the user specified it — use placeholders or generic wording instead."
    ),
    "research": (
        "Optimize for research tasks. Prefer objective, scope, context, sources, depth, "
        "output format, and evaluation criteria. Do not invent facts or citations."
    ),
    "chatgpt": (
        "Use clear role/task/format structure suitable for ChatGPT-style assistants. "
        "Prefer explicit sections when helpful. This is a light structural preference, "
        "not a claim of proprietary optimization."
    ),
    "claude": (
        "Prefer explicit instructions and structured sections; XML-like tags are optional "
        "when they improve clarity. This is a light structural preference, not a proprietary claim."
    ),
    "gemini": (
        "Prefer clear task framing and concise constraints suitable for Gemini-style models. "
        "This is a light structural preference, not a proprietary claim."
    ),
    "custom": (
        "Apply general enhancement principles without model-specific claims."
    ),
}


def get_target_pack(target: TargetType | str) -> str:
    key = target.value if isinstance(target, TargetType) else str(target)
    return PACKS.get(key, PACKS["general"])
