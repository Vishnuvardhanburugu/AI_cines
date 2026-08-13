from app.services.prompt_enhancement.image_prompt_packer import (
    is_mythic_epic,
    pack_image_prompt,
    prefer_portrait,
)
from app.services.prompt_enhancement.cinematic_composer import compose_cinematic


def test_packer_strips_meta_and_keeps_hanuman():
    raw = (
        "Create a photoreal cinematic still frame of Hanuman. "
        "Depict the core action described by the user: generate an image the Hanuman. "
        "Set in an environment that matches the user's scene with clear geographic and atmospheric cues."
    )
    packed = pack_image_prompt(raw, portrait=True)
    lower = packed.lower()
    assert "depict the core action" not in lower
    assert "described by the user" not in lower
    assert "hanuman" in lower
    assert "photoreal" in lower or "live-action" in lower
    assert "9:16" in lower or "vertical" in lower
    assert "cartoon" in lower


def test_prefer_portrait_for_mythic():
    w, h = prefer_portrait("Hanuman burning Lanka", 1024, 576)
    assert h > w
    assert is_mythic_epic("hanuman on a cliff")


def test_composer_thin_hanuman_image_no_meta_action():
    result = compose_cinematic("generate an image the Hanuman", kind="image")
    blob = (result.enhanced_prompt + "\n" + result.structured_prompt).lower()
    assert "depict the core action described by the user" not in blob
    assert "hanuman" in blob
    assert "9:16" in blob or "vertical" in blob
    assert "cliff" in blob or "burn" in blob or "fire" in blob
