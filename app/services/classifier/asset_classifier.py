"""Auction asset classification."""


class AssetClassifier:
    """Keyword-based fallback asset classifier."""

    IMMOVABLE_KEYWORDS = {
        "flat": "Flat",
        "apartment": "Apartment",
        "house": "Residential House",
        "land": "Land",
        "plot": "Land",
        "factory": "Factory",
        "building": "Building",
        "property": "Property",
    }
    MOVABLE_KEYWORDS = {
        "gold": "Gold",
        "vehicle": "Vehicle",
        "car": "Vehicle",
        "machine": "Machinery",
        "machinery": "Machinery",
        "scrap": "Scrap",
        "stock": "Stock",
    }

    def classify_asset(self, text: str) -> tuple[str, str]:
        """Return asset category and movable/immovable value."""
        lower = text.lower()
        for keyword, label in self.IMMOVABLE_KEYWORDS.items():
            if keyword in lower:
                return label, "Immovable"
        for keyword, label in self.MOVABLE_KEYWORDS.items():
            if keyword in lower:
                return label, "Movable"
        return "", ""

