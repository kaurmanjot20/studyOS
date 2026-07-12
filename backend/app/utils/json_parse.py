"""Tolerant JSON extraction from LLM output.

Models often wrap JSON in prose or ```json fences. This pulls out the first JSON object
and parses it, raising ValueError if nothing valid is found.
"""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned).rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)
