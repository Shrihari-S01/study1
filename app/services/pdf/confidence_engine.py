"""
Confidence Engine for PDF Processing Pipeline.
Applies hierarchical confidence scoring and prevents higher-confidence values from being overwritten by lower-confidence values.
"""

from app.core.logger import get_logger

logger = get_logger(__name__)


class ConfidenceEngine:
    """
    Confidence scoring matrix for field values.
    """

    SCORES = {
        "native_text": 1.00,
        "structured_section": 0.99,
        "regex": 0.98,
        "ocr": 0.93,
        "vision": 0.90,
        "llm": 0.60
    }

    def assign_confidence(self, field_name: str, source_type: str) -> float:
        """
        Return confidence score for a given source type.
        """
        score = self.SCORES.get(source_type.lower(), 0.80)
        return score

    def merge_field(self, current_val, new_val, current_source: str, new_source: str):
        """
        Higher-confidence values must never be overwritten by lower-confidence values.
        """
        curr_score = self.SCORES.get(current_source.lower(), 0.0) if current_val else 0.0
        new_score = self.SCORES.get(new_source.lower(), 0.0) if new_val else 0.0

        if new_score > curr_score and new_val not in (None, "", 0, 0.0):
            return new_val, new_source
        return current_val, current_source
