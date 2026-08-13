"""Internal pipeline domain models (not all exposed to clients)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EnhanceMode(str, Enum):
    MINIMAL = "minimal"
    BALANCED = "balanced"
    ADVANCED = "advanced"


class TargetType(str, Enum):
    GENERAL = "general"
    IMAGE = "image"
    VIDEO = "video"
    CODING = "coding"
    RESEARCH = "research"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    CUSTOM = "custom"


class EnhanceOperation(str, Enum):
    MORE_SPECIFIC = "more_specific"
    CONCISE = "concise"
    CREATIVE = "creative"
    PROFESSIONAL = "professional"
    ADD_CONSTRAINTS = "add_constraints"
    OPTIMIZE_IMAGE = "optimize_image"
    OPTIMIZE_VIDEO = "optimize_video"
    OPTIMIZE_CODING = "optimize_coding"


class IntentModel(BaseModel):
    """Structured intent — used internally only; never returned as CoT."""

    goal: str = ""
    subject: str = ""
    action: str = ""
    context: str = ""
    constraints: list[str] = Field(default_factory=list)
    desired_output: str = ""
    style: str = ""
    audience: str = ""
    known_details: list[str] = Field(default_factory=list)
    missing_details: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class AnalyzeResult(BaseModel):
    category: str = "general"
    intent: IntentModel = Field(default_factory=IntentModel)
    material_gaps: list[str] = Field(default_factory=list)
    quality_before: int = 0
    analysis_summary: str = ""


class EnhanceResult(BaseModel):
    enhanced_prompt: str
    structured_prompt: Optional[str] = None
    changes: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    explanation: str = ""
    clarification_questions: list[str] = Field(default_factory=list)
    quality_after: int = 0


class ValidationResult(BaseModel):
    passed: bool = True
    issues: list[str] = Field(default_factory=list)
    unsupported_assumptions: list[str] = Field(default_factory=list)
    should_degrade: bool = False
