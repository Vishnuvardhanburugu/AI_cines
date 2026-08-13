"""Multi-stage enhancement pipeline: analyze → enhance → validate (+ retry/degrade)."""

from __future__ import annotations

from app.api.schemas import EnhanceRequest, EnhanceResponse
from app.models.domain import EnhanceMode
from app.providers.base import LLMProvider, LLMProviderError, get_provider
from app.services.prompt_analysis.analyze import analyze_prompt
from app.services.prompt_enhancement.enhance import enhance_prompt
from app.services.validation.validate import validate_enhancement


class EnhancementPipeline:
    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or get_provider()

    async def run(self, request: EnhanceRequest) -> EnhanceResponse:
        prompt = request.prompt.strip()

        analysis = await analyze_prompt(self.provider, prompt, request.target)

        enhance = await enhance_prompt(
            self.provider,
            prompt,
            analysis,
            request.mode,
            request.target,
            operations=request.operations,
        )

        validation = await validate_enhancement(
            self.provider, prompt, enhance, analysis, use_llm=True
        )

        if not validation.passed:
            # One constrained regenerate
            enhance = await enhance_prompt(
                self.provider,
                prompt,
                analysis,
                request.mode,
                request.target,
                operations=request.operations,
                validation_issues=validation.issues + validation.unsupported_assumptions,
            )
            validation = await validate_enhancement(
                self.provider, prompt, enhance, analysis, use_llm=True
            )

            if not validation.passed:
                # Degrade to minimal
                enhance = await enhance_prompt(
                    self.provider,
                    prompt,
                    analysis,
                    EnhanceMode.MINIMAL,
                    request.target,
                    operations=[],
                    validation_issues=validation.issues,
                    force_minimal=True,
                )
                # Re-score already done inside enhance_prompt
                if validation.unsupported_assumptions:
                    # Surface remaining concerns without blocking
                    enhance.assumptions = list(
                        dict.fromkeys(
                            enhance.assumptions + validation.unsupported_assumptions
                        )
                    )

        analysis_text = analysis.analysis_summary
        if not analysis_text and analysis.material_gaps:
            analysis_text = (
                "Could improve: " + ", ".join(analysis.material_gaps[:5]) + "."
            )

        explanation = enhance.explanation
        if getattr(self.provider, "used_fallback", False):
            note = (
                "Gemini/API quota was hit, so this enhancement used the offline "
                "composer so you can continue to Generate image."
            )
            explanation = f"{explanation} {note}".strip() if explanation else note

        return EnhanceResponse(
            original_prompt=prompt,
            enhanced_prompt=enhance.enhanced_prompt,
            structured_prompt=enhance.structured_prompt,
            category=analysis.category,
            quality_before=analysis.quality_before,
            quality_after=enhance.quality_after,
            changes=enhance.changes,
            assumptions=enhance.assumptions,
            explanation=explanation,
            clarification_questions=enhance.clarification_questions,
            analysis=analysis_text or None,
        )


async def run_enhancement(request: EnhanceRequest) -> EnhanceResponse:
    try:
        pipeline = EnhancementPipeline()
        return await pipeline.run(request)
    except LLMProviderError:
        raise
    except Exception as exc:  # pragma: no cover - safety net
        raise LLMProviderError(
            f"Enhancement pipeline failed unexpectedly: {exc}",
            status_code=500,
        ) from exc
