"""Robust JSON extraction from Claude output (handles code fences)."""

import json
import re
from typing import Any


class JSONParseError(Exception):
    """Raised when JSON cannot be extracted from LLM output."""

    pass


def parse_llm_json(text: str) -> Any:
    """Parse JSON from LLM output, stripping markdown code fences if present.

    Tries direct parse first, then strips ```json ... ``` fences.
    Raises JSONParseError on failure.
    """
    # Pass 1: try direct parse
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Pass 2: strip markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    raise JSONParseError(
        f"Could not parse JSON from LLM output. First 200 chars: {text[:200]}"
    )
