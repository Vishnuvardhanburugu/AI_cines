from app.models.domain import AnalyzeResult, EnhanceResult, IntentModel
from app.services.validation.guards import run_rule_guards


def test_coding_invented_stack_fails_without_assumption():
    analysis = AnalyzeResult(
        category="coding",
        intent=IntentModel(known_details=["Python", "API", "image"], constraints=[]),
        quality_before=40,
    )
    enhance = EnhanceResult(
        enhanced_prompt="Build a FastAPI service using YOLO and PostgreSQL for image detection.",
        assumptions=[],
        quality_after=70,
    )
    result = run_rule_guards(
        "Create a Python API that receives an image and detects objects.",
        enhance,
        analysis,
        40,
    )
    assert not result.passed
    assert any("FastAPI" in i or "fastapi" in i.lower() for i in result.issues + result.unsupported_assumptions)


def test_leave_email_invented_date_fails():
    analysis = AnalyzeResult(
        category="general",
        intent=IntentModel(known_details=["email", "manager", "leave"]),
        quality_before=35,
    )
    enhance = EnhanceResult(
        enhanced_prompt="Write an email asking for leave from January 15 to January 20 because I am sick.",
        assumptions=[],
        quality_after=60,
    )
    result = run_rule_guards(
        "Write an email asking my manager for leave.",
        enhance,
        analysis,
        35,
    )
    assert not result.passed
