"""LLM response parsing."""

import json
import re
from typing import Any

from app.core.exceptions import ProcessingError


class LLMParser:
    """Parse JSON from LLM responses."""

    def parse_json(self, content: str) -> dict[str, Any]:
        """Return a dict from a raw LLM message."""
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            text = match.group(0)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProcessingError("Groq did not return valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ProcessingError("Groq JSON response must be an object")
        return parsed

