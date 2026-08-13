"""HTTP routes."""

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.schemas import (
    EnhanceRequest,
    EnhanceResponse,
    GenerateImageRequest,
    GenerateImageResponse,
    HealthResponse,
)
from app.core.config import get_settings
from app.core.security import validate_prompt_input
from app.providers.base import LLMProviderError
from app.services.image_generation import generate_image
from app.services.pipeline import run_enhancement
from app.utils.logging import log_request_meta
from fastapi import HTTPException

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", provider=settings.llm_provider)


@router.post("/enhance", response_model=EnhanceResponse)
@limiter.limit(get_settings().rate_limit)
async def enhance(request: Request, body: EnhanceRequest) -> EnhanceResponse:
    cleaned = validate_prompt_input(body.prompt)
    body = body.model_copy(update={"prompt": cleaned})
    log_request_meta(
        prompt_len=len(cleaned),
        mode=body.mode.value,
        target=body.target.value,
    )

    try:
        return await run_enhancement(body)
    except LLMProviderError as exc:
        status = exc.status_code or 502
        raise HTTPException(status_code=status, detail=exc.message) from exc


@router.post("/generate-image", response_model=GenerateImageResponse)
@limiter.limit(get_settings().rate_limit)
async def generate_image_route(
    request: Request, body: GenerateImageRequest
) -> GenerateImageResponse:
    try:
        return await generate_image(body)
    except LLMProviderError as exc:
        status = exc.status_code or 502
        raise HTTPException(status_code=status, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Image generation failed unexpectedly. Please try again.",
        ) from exc
