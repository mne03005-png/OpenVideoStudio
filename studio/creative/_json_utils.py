"""Tiny shared helper for extracting JSON from an LLM response. Models
routinely wrap JSON in ```json fences or add a stray sentence before/after
it — this strips that reliably rather than each caller reinventing it."""
from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict:
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        # No fence: take the substring between the first { or [ and the matching last } or ]
        start = min((i for i in (text.find("{"), text.find("[")) if i != -1), default=-1)
        end = max(text.rfind("}"), text.rfind("]"))
        if start != -1 and end != -1:
            text = text[start:end + 1]
    return json.loads(text)
