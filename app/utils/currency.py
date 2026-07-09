"""Currency formatting helpers."""

import re


def normalize_currency(value: str | None) -> str:
    """Normalize rupee values without losing the original amount."""
    if not value:
        return ""
    cleaned = value.strip().replace("INR", "Rs.").replace("₹", "Rs. ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned.lower().startswith("rs"):
        return cleaned
    return f"Rs. {cleaned}"

