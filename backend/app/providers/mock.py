"""Deterministic mock provider for tests and offline demos."""

import re
from typing import Any

from app.services.prompt_enhancement.cinematic_composer import compose_cinematic


class MockProvider:
    def name(self) -> str:
        return "mock"

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        system_l = system.lower()
        user_l = user.lower()

        if "prompt-enhancement validator" in system_l or (
            "unsupported_assumptions" in system_l and '"pass"' in system_l
        ):
            return {
                "pass": True,
                "issues": [],
                "unsupported_assumptions": [],
            }

        if "prompt analysis engine" in system_l or "intent extraction" in system_l:
            return self._analyze(user)

        if "semantic prompt enhancer" in system_l or "enhanced_prompt" in system_l:
            return self._enhance(user)

        if "material_gaps" in user_l:
            return self._analyze(user)

        return {"ok": True}

    def _extract_prompt(self, user: str) -> str:
        match = re.search(r"ORIGINAL PROMPT:\s*(.+?)(?:\n\n|\nMODE:|\nTARGET:|$)", user, re.S)
        if match:
            return match.group(1).strip()
        match = re.search(r'"prompt"\s*:\s*"([^"]+)"', user)
        if match:
            return match.group(1)
        lines = [ln.strip() for ln in user.splitlines() if ln.strip()]
        return lines[-1] if lines else "prompt"

    def _target_from_user(self, user: str) -> str:
        match = re.search(r"TARGET:\s*(\w+)", user, re.I)
        if match:
            return match.group(1).lower()
        if "target pack" in user.lower() and "video" in user.lower():
            return "video"
        return "general"

    def _analyze(self, user: str) -> dict[str, Any]:
        prompt = self._extract_prompt(user).lower()
        target = self._target_from_user(user)
        category = "general"
        if target in {"video", "image", "coding", "research"}:
            category = target
        elif any(w in prompt for w in ("video", "cinematic", "footage", "clip", "hanuman", "lanka")):
            category = "video"
        elif any(w in prompt for w in ("image", "photo", "illustration", "picture")):
            category = "image"
        elif any(w in prompt for w in ("python", "api", "code", "function", "typescript")):
            category = "coding"
        elif any(w in prompt for w in ("research", "sources", "literature")):
            category = "research"
        elif any(w in prompt for w in ("email", "manager", "leave")):
            category = "general"

        gaps = []
        if category == "video":
            gaps = ["environment", "camera movement", "atmosphere", "visual style"]
        elif category == "image":
            gaps = ["composition", "lighting", "camera", "style"]
        elif category == "coding":
            gaps = ["framework", "input/output format", "error handling", "tests"]
        elif "email" in prompt or "leave" in prompt:
            gaps = ["dates", "duration", "reason", "tone"]
        else:
            gaps = ["output format", "constraints", "audience"]

        return {
            "category": category,
            "goal": "Fulfill the user's request",
            "subject": prompt[:80],
            "action": "create" if "create" in prompt or "make" in prompt else "produce",
            "context": "",
            "constraints": [],
            "desired_output": category,
            "style": "",
            "audience": "",
            "known_details": [self._extract_prompt(user)[:120]],
            "missing_details": gaps,
            "ambiguities": ["underspecified details"],
            "material_gaps": gaps,
            "analysis_summary": f"Underspecified {category} request; missing useful dimensions.",
        }

    def _enhance(self, user: str) -> dict[str, Any]:
        prompt = self._extract_prompt(user)
        lower = prompt.lower()
        target = self._target_from_user(user)
        mode_minimal = re.search(r"\bMODE:\s*minimal\b", user, re.I) is not None

        if mode_minimal:
            enhanced = prompt.strip()
            if not enhanced.endswith("."):
                enhanced += "."
            return {
                "enhanced_prompt": enhanced,
                "structured_prompt": None,
                "changes": ["Minor clarity cleanup"],
                "assumptions": [],
                "explanation": "Kept wording close to the original while fixing clarity.",
                "clarification_questions": [],
            }

        # Visual / cinematic path — never return meta boilerplate
        visual = target in {"video", "image"} or any(
            w in lower
            for w in (
                "video",
                "cinematic",
                "hanuman",
                "lanka",
                "film",
                "shot",
                "scene",
                "draw",
                "image",
            )
        )
        if visual and not (
            "python" in lower and ("api" in lower or "function" in lower)
        ):
            kind = "image" if target == "image" or lower.startswith("draw") else "video"
            composed = compose_cinematic(prompt, kind=kind)
            return {
                "enhanced_prompt": composed.enhanced_prompt,
                "structured_prompt": composed.structured_prompt,
                "changes": composed.changes,
                "assumptions": composed.assumptions,
                "explanation": composed.explanation,
                "clarification_questions": composed.clarification_questions,
            }

        if "futuristic city" in lower or ("video" in lower and "city" in lower):
            composed = compose_cinematic(prompt, kind="video")
            return {
                "enhanced_prompt": composed.enhanced_prompt,
                "structured_prompt": composed.structured_prompt,
                "changes": composed.changes,
                "assumptions": composed.assumptions,
                "explanation": composed.explanation,
                "clarification_questions": composed.clarification_questions,
            }

        if "python" in lower and ("api" in lower or "detect" in lower or "object" in lower):
            return {
                "enhanced_prompt": (
                    "Create a Python web API that accepts an image upload and returns detected objects. "
                    "Specify: request content type (multipart image upload), response JSON schema "
                    "(label, confidence, bounding box), validation and error handling for invalid files, "
                    "and basic performance expectations. Use a suitable web framework and a suitable "
                    "object-detection approach — do not hard-require a specific stack unless chosen. "
                    "Include edge cases (empty file, unsupported format) and a brief testing checklist."
                ),
                "structured_prompt": None,
                "changes": [
                    "Defined input and output shape",
                    "Added error handling and edge cases",
                    "Added testing expectations",
                    "Avoided locking to a specific framework or detector",
                ],
                "assumptions": [],
                "explanation": (
                    "Your original prompt stated the objective and language but lacked I/O, errors, "
                    "and evaluation criteria. Those were added without inventing a specific stack."
                ),
                "clarification_questions": [
                    "Preferred web framework?",
                    "Preferred detection model or cloud vision API?",
                ],
            }

        if "email" in lower and ("leave" in lower or "manager" in lower):
            return {
                "enhanced_prompt": (
                    "Write a professional email to my manager requesting leave. "
                    "Use a clear subject line, polite opening, a concise request for time off, "
                    "placeholders for start date, end date, and reason (do not invent them), "
                    "an offer to hand off work, and a courteous closing."
                ),
                "structured_prompt": None,
                "changes": [
                    "Clarified professional tone",
                    "Defined email structure",
                    "Used placeholders for dates and reason instead of inventing them",
                ],
                "assumptions": [],
                "explanation": (
                    "Preserved the leave-request purpose and added structure and tone without "
                    "inventing dates or reasons."
                ),
                "clarification_questions": [
                    "What dates are you requesting?",
                    "Do you want to include a reason?",
                ],
            }

        # Non-visual generic: still avoid useless meta boilerplate
        return {
            "enhanced_prompt": (
                f"{prompt.strip().rstrip('.')}. "
                "State the goal clearly, include relevant constraints, and specify the desired output format."
            ),
            "structured_prompt": None,
            "changes": [
                "Clarified expected output format",
                "Added constraint reminder without inventing requirements",
            ],
            "assumptions": [],
            "explanation": "Added light structure guidance while preserving the original request.",
            "clarification_questions": [],
        }
