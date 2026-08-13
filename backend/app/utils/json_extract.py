"""Robust JSON extraction from model outputs."""

import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("Empty model content")

    cleaned = text.strip()
    # Strip markdown fences if present
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if fence:
        cleaned = fence.group(1).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
        raise ValueError("JSON root is not an object")
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        data = json.loads(cleaned[start : end + 1])
        if not isinstance(data, dict):
            raise ValueError("JSON root is not an object")
        return data
