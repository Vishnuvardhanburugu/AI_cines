"""Deterministic cinematic master-prompt composer for video/image targets.

Used by mock mode and as a quality guardrail when LLM output is thin/meta.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


META_BOILERPLATE_MARKERS = (
    "provide a clear, complete response",
    "state assumptions explicitly if details are missing",
    "structure the output for readability",
)


@dataclass
class CinematicComposeResult:
    structured_prompt: str
    enhanced_prompt: str
    changes: list[str]
    assumptions: list[str]
    explanation: str
    clarification_questions: list[str]


def is_thin_or_meta_enhancement(original: str, enhanced: str) -> bool:
    if not enhanced or not enhanced.strip():
        return True
    lower = enhanced.lower()
    if any(m in lower for m in META_BOILERPLATE_MARKERS):
        return True
    if len(enhanced.split()) <= len(original.split()) + 12:
        cinematic_cues = ("camera", "lighting", "cinematic", "shot", "atmosphere", "photoreal")
        if not any(c in lower for c in cinematic_cues):
            return True
    return False


def compose_cinematic(prompt: str, *, kind: str = "video") -> CinematicComposeResult:
    cleaned = _cleanup_text(prompt)
    lower = cleaned.lower()
    is_video = kind.lower() in {"video", "video_generation"}
    theme = _detect_theme(lower)

    subject = _infer_subject(cleaned, theme)
    action = _infer_action(cleaned, theme)
    setting = _infer_setting(cleaned, theme)
    style_note = _infer_style(cleaned)

    if theme == "mythic":
        camera = (
            "Slow cinematic tracking shot that reveals mythic scale, then a controlled push-in on the hero; "
            "wide establishing frames for geography."
            if is_video
            else (
                "Vertical 9:16 IMAX-scale composition, low-angle heroic framing from a rocky cliff overlook; "
                "subject large in frame with the burning coast stretching below."
            )
        )
        lighting = (
            "Dramatic dual lighting: warm practical firelight from the burning city below mixed with "
            "cool crescent moonlight; volumetric smoke, ember particles, and high-contrast rim light."
        )
        atmosphere = (
            "Dense mythic night air: heat haze over flames, drifting ash, coastal wind, "
            "storm clouds, and a tense epic mood."
        )
        motion = (
            "Believable body mechanics and cloth/fur physics; continuous fire with trailing embers; "
            "subtle parallax and camera inertia; no discontinuous jump cuts."
            if is_video
            else "Frozen peak heroic still with implied motion in fire, fabric, smoke trails, and wind."
        )
        style = (
            f"{style_note} Photoreal live-action epic cinema, grounded mythological spectacle, "
            "rich fur/metal/fabric texture detail. Avoid cartoon, anime, comic-book, or stylized illustration looks."
        )
        assumptions = [
            "Night-time dual lighting (moon + fire) for epic contrast",
            "Photoreal live-action look (explicitly non-cartoon) as the visual baseline",
            "Vertical 9:16 heroic cliff-overlook composition for stills",
        ]
        if "rama" in lower:
            assumptions.append(
                "Parallel beat with Rama sensing Hanuman's approach (as implied by the user)"
            )
        if "hanuman" in lower and "mace" not in lower and "gada" not in lower:
            assumptions.append("Ornate golden mace (gada) and armor as classic heroic iconography")
        questions = [
            "Portrait 9:16 still or landscape widescreen?",
            "Should Rama appear on screen, or only as a sensed/off-screen beat?",
            "Classical epic film look or grounded historical realism?",
        ]
    elif theme == "scifi":
        camera = (
            "Slow cinematic tracking shot through the city, then a gradual tilt toward the skyline; "
            "optional aerial reveal for scale."
            if is_video
            else "Wide skyline composition with leading lines through architecture; slight low angle for scale."
        )
        lighting = (
            "Cool neon accents with volumetric haze, reflective glass/metal surfaces, "
            "and believable urban night illumination."
        )
        atmosphere = (
            "Dense but grounded futuristic air: light fog, wet-street reflections, distant traffic glow."
        )
        motion = (
            "Smooth vehicle motion, subtle camera inertia, and temporal consistency across the frame; "
            "no chaotic whip-pans."
            if is_video
            else "Implied motion via light trails and layered depth."
        )
        style = (
            f"{style_note} Photoreal cinematic sci-fi, grounded near-future realism, "
            "high detail. Avoid cartoon or overly glossy game-CGI looks."
        )
        assumptions = [
            "Night-or-dusk lighting for neon readability",
            "Slow tracking shot as default camera language",
            "Grounded futuristic style rather than fantasy surrealism",
        ]
        questions = [
            "Day or night?",
            "Street-level, drone, or rooftop camera?",
            "Any specific architecture or color palette?",
        ]
    else:
        camera = (
            "Clear cinematic framing with a deliberate camera move that reveals subject and environment."
            if is_video
            else "Strong composition with clear subject hierarchy and depth."
        )
        lighting = "Motivated cinematic lighting with readable contrast and atmospheric depth."
        atmosphere = "Immersive environment detail that supports the subject's mood without clutter."
        motion = (
            "Natural motion, consistent physics, and smooth camera continuity."
            if is_video
            else "Implied motion through pose, fabric, and environmental cues."
        )
        style = (
            f"{style_note} Photoreal cinematic look with coherent visual style. "
            "Avoid cartoon unless the user requested it."
        )
        assumptions = [
            "Photoreal cinematic baseline unless the user specified another style",
            "Camera and lighting chosen to support clarity and mood",
        ]
        questions = [
            "Any preferred camera move or lens feel?",
            "Time of day / weather?",
            "Any hard constraints to avoid?",
        ]

    negatives = (
        "No cartoon, no anime, no comic ink outlines, no plastic CGI faces, "
        "no text overlays, no watermark, no unrelated characters."
        if "cartoon" in lower or "real" in lower or theme == "mythic"
        else "No text overlays, no watermark, no unrelated subjects, no chaotic framing."
    )

    structured = "\n".join(
        [
            f"Subject: {subject}",
            f"Action: {action}",
            f"Setting: {setting}",
            f"Camera / Shot: {camera}",
            f"Lighting: {lighting}",
            f"Atmosphere: {atmosphere}",
            f"Motion / Continuity: {motion}",
            f"Style / Realism: {style}",
            f"Negatives / Constraints: {negatives}",
        ]
    )

    medium = "cinematic video sequence" if is_video else "cinematic still frame"
    paragraph = (
        f"Create a photoreal {medium} of {subject}. {action} "
        f"Set in {setting}. {camera} {lighting} {atmosphere} {motion} "
        f"{style} {negatives}"
    )

    changes = [
        "Expanded into a cinematic master prompt with labeled production sections",
        "Added camera direction and shot language",
        "Added lighting, atmosphere, and style constraints",
        "Added negatives / constraints",
        "Produced a ready-to-paste flowing cinematic paragraph",
    ]
    if is_video:
        changes.append("Added motion and temporal continuity guidance")

    return CinematicComposeResult(
        structured_prompt=structured,
        enhanced_prompt=paragraph,
        changes=changes,
        assumptions=assumptions,
        explanation=(
            "Your idea defined the core subject and action but lacked cinematic production detail. "
            "I preserved that intent and added camera, lighting, atmosphere, realism, and negatives."
        ),
        clarification_questions=questions,
    )


def _detect_theme(lower: str) -> str:
    if any(
        w in lower
        for w in ("hanuman", "rama", "lanka", "kishkindha", "ramayan", "myth", "vanara", "gada")
    ):
        return "mythic"
    if any(w in lower for w in ("futuristic", "cyber", "neon", "sci-fi", "scifi", "flying car")):
        return "scifi"
    if "city" in lower and ("future" in lower or "video" in lower):
        return "scifi"
    return "general"


def _cleanup_text(text: str) -> str:
    t = re.sub(r"\s+", " ", text.strip())
    replacements = {
        r"\bteh\b": "the",
        r"\bkiskindha\b": "Kishkindha",
        r"\bkishkindha kanda\b": "Kishkindha Kanda",
        r"\blanka\b": "Lanka",
        r"\bhanuman\b": "Hanuman",
        r"\blord sri rama\b": "Lord Sri Rama",
        r"\bsri rama\b": "Sri Rama",
    }
    for pat, rep in replacements.items():
        t = re.sub(pat, rep, t, flags=re.I)
    return t


def _infer_subject(text: str, theme: str) -> str:
    lower = text.lower()
    if theme == "mythic":
        parts = []
        if "hanuman" in lower:
            parts.append("Hanuman, the mighty vanara warrior")
        if "rama" in lower:
            parts.append("Lord Sri Rama")
        if parts:
            return " and ".join(parts)
    if "futuristic city" in lower or ("city" in lower and "futuristic" in lower):
        return "a futuristic megacity skyline"
    if "city" in lower:
        return "a cityscape"
    clause = re.split(r"[.!?]", text)[0].strip()
    # Strip leading "make a video of" / "create a video of"
    clause = re.sub(
        r"^(make|create|generate|draw)\s+(a\s+)?(cinematic\s+)?(video|image|clip|scene)\s+(of\s+)?",
        "",
        clause,
        flags=re.I,
    ).strip()
    return clause[:160] if clause else "the primary subject from the user's idea"


def _infer_action(text: str, theme: str) -> str:
    lower = text.lower()
    if theme == "mythic":
        bits = []
        if "hanuman" in lower and ("burn" in lower or "fire" in lower or "tail" in lower):
            bits.append(
                "Hanuman stands as a mighty vanara warrior with his presence tied to the burning of Lanka — "
                "tail/fire energy implied, overlooking the city as flames consume rooftops and harbor"
            )
        elif "hanuman" in lower:
            bits.append(
                "Hanuman stands heroically on a rocky cliff, holding a golden mace, "
                "gazing over a burning coastal fortress-city at night"
            )
        if "rama" in lower and ("sens" in lower or "arrival" in lower or "kishkindha" in lower):
            bits.append(
                "meanwhile Lord Sri Rama senses Hanuman's triumphant approach toward Kishkindha Kanda, "
                "his expression shifting with recognition and resolve"
            )
        if bits:
            return "; ".join(bits) + "."
    if "futuristic city" in lower or ("city" in lower and theme == "scifi"):
        return (
            "Reveal the living city: elevated traffic lanes, glowing towers, and atmospheric depth "
            "as the camera moves through the environment."
        )
    # Never emit "Depict the core action described by the user"
    clause = re.sub(
        r"^(make|create|generate|draw)\s+(a\s+)?(cinematic\s+)?(video|image|clip|scene)\s+(of\s+|the\s+)?",
        "",
        text,
        flags=re.I,
    ).strip()
    return f"Show {clause} with clear peak dramatic staging and readable subject action."


def _infer_setting(text: str, theme: str) -> str:
    lower = text.lower()
    if theme == "mythic":
        if "lanka" in lower and "kishkindha" in lower:
            return (
                "dual geography — night-time Lanka in flames (stone fortresses, carved towers, coastal haze) "
                "and Kishkindha's forested kingdom where Rama awaits news"
            )
        if "lanka" in lower or "hanuman" in lower:
            return (
                "ancient coastal Lanka at night: rocky cliff overlook above a burning fortress-city and harbor, "
                "ships and walls lit by raging fire under storm clouds"
            )
        if "kishkindha" in lower:
            return "Kishkindha Kanda: rugged forest kingdom under a vast mythic sky"
    if theme == "scifi":
        return (
            "a futuristic metropolitan cityscape with towering glass-and-metal architecture, "
            "elevated transit, and layered urban density"
        )
    return "a clear cinematic environment with readable geography, depth, and atmospheric cues"


def _infer_style(text: str) -> str:
    lower = text.lower()
    if "not cartoon" in lower or "real" in lower or "photoreal" in lower or "realistic" in lower:
        return "Strictly photoreal and non-cartoonish."
    return "High cinematic realism."
