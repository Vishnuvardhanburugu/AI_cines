"""Compress enhanced prompts into dense Gemini-oriented still-image prompts."""

from __future__ import annotations

import re


META_PHRASES = (
    r"depict the core action described by the user[:\s]*",
    r"described by the user",
    r"provide a clear, complete response[^.]*\.?",
    r"state assumptions explicitly[^.]*\.?",
    r"structure the output for readability[^.]*\.?",
    r"generate an image the\s+",
    r"an environment that matches the user's scene with clear geographic and atmospheric cues\.?",
)


def is_mythic_epic(prompt: str) -> bool:
    lower = prompt.lower()
    return any(
        w in lower
        for w in ("hanuman", "rama", "lanka", "kishkindha", "ramayan", "vanara", "mythic", "gada")
    )


def prefer_portrait(prompt: str, width: int, height: int) -> tuple[int, int]:
    """Mythic/epic stills default to 9:16 unless caller already requested portrait."""
    if height > width:
        return width, height
    if is_mythic_epic(prompt) or "9:16" in prompt.lower() or "vertical" in prompt.lower():
        return 768, 1344
    return width, height


def pack_image_prompt(prompt: str, *, portrait: bool = False) -> str:
    """
    Produce a short, dense still prompt for Gemini/Pollinations.
    Strips meta filler and reinforces photoreal cinematic constraints.
    """
    text = " ".join(prompt.split()).strip()
    for pat in META_PHRASES:
        text = re.sub(pat, " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" .")

    mythic = is_mythic_epic(text)
    aspect = "9:16 vertical cinematic composition" if portrait or mythic else "16:9 cinematic landscape"

    # If prompt collapsed to nearly nothing, rebuild a strong mythic still
    if mythic and len(text) < 80:
        text = (
            "Photoreal live-action still of Hanuman, mighty vanara warrior, muscular fur detail, "
            "ornate golden armor and crown, holding a golden mace (gada), standing on a rocky cliff "
            "overlook above a burning coastal city at night with ships and fortress walls in flames"
        )
    elif mythic:
        # Ensure key reference beats are present
        additions = []
        lower = text.lower()
        if "cliff" not in lower and "overlook" not in lower:
            additions.append("standing on a rocky cliff overlook")
        if "burn" not in lower and "fire" not in lower and "flame" not in lower:
            if "lanka" in lower or "hanuman" in lower:
                additions.append("burning coastal city and harbor below engulfed in flames")
        if "moon" not in lower:
            additions.append("crescent moonlight mixed with warm firelight")
        if "mace" not in lower and "gada" not in lower and "hanuman" in lower:
            additions.append("holding an ornate golden mace")
        if additions:
            text = text.rstrip(".") + ". " + ", ".join(additions)

    packed = (
        f"{text}. Aspect ratio {aspect}, low-angle heroic framing, photoreal live-action "
        f"epic cinema, rich fur/metal/fabric texture, volumetric smoke and ember particles, "
        f"high-contrast rim light. No cartoon, no anime, no comic ink, no plastic CGI faces, "
        f"no text overlay, no watermark."
    )
    packed = re.sub(r"\s+", " ", packed).strip()
    # Soft cap for URL / API limits
    if len(packed) > 1400:
        packed = packed[:1399].rstrip() + "…"
    return packed
