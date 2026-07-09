"""Auction type classification."""


class AuctionClassifier:
    """Classify auction type from notice text."""

    def classify(self, text: str) -> str:
        lower = text.lower()
        if "e-auction" in lower or "e auction" in lower or "online auction" in lower:
            return "E-Auction"
        if "bank auction" in lower or "sale notice" in lower or "sarfaesi" in lower:
            return "Bank Auction"
        return "Auction"

