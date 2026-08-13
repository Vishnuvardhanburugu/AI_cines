"""Input validation helpers. API keys never leave the backend."""

from fastapi import HTTPException, status

from app.core.config import get_settings


def validate_prompt_input(prompt: str) -> str:
    """Normalize and validate user prompt. Raises HTTPException on failure."""
    settings = get_settings()
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt is required.",
        )
    cleaned = prompt.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty. Enter a rough idea or instruction to enhance.",
        )
    if len(cleaned) > settings.max_prompt_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Prompt is too long ({len(cleaned)} characters). "
                f"Maximum allowed is {settings.max_prompt_length}."
            ),
        )
    return cleaned
