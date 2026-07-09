"""Possession type classification."""


class PossessionClassifier:
    """Detect possession type from auction notice text."""

    def classify(self, text: str) -> str:
        lower = text.lower()
        has_symbolic = "symbolic possession" in lower
        has_physical = "physical possession" in lower
        if has_symbolic and has_physical:
            return "Symbolic / Physical Possession"
        if has_symbolic:
            return "Symbolic Possession"
        if has_physical:
            return "Physical Possession"
        return ""

