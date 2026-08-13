"""Public API request/response schemas."""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.domain import EnhanceMode, EnhanceOperation, TargetType


class EnhanceRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=12000)
    mode: EnhanceMode = EnhanceMode.BALANCED
    target: TargetType = TargetType.GENERAL
    operations: list[EnhanceOperation] = Field(default_factory=list)


class EnhanceResponse(BaseModel):
    original_prompt: str
    enhanced_prompt: str
    structured_prompt: Optional[str] = None
    category: str
    quality_before: int
    quality_after: int
    changes: list[str]
    assumptions: list[str]
    explanation: str
    clarification_questions: list[str] = Field(default_factory=list)
    analysis: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    provider: str


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=12000)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=576, ge=256, le=2048)
    # auto | gemini | huggingface | pollinations | mock
    provider: str = Field(default="auto")
    # auto | portrait | landscape
    aspect: str = Field(default="auto")


class GenerateImageResponse(BaseModel):
    image_url: str
    provider: str
    prompt_used: str
