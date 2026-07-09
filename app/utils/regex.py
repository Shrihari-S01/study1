"""Regex-based deterministic extraction helpers."""

import re

from app.schemas.extraction import RegexExtraction

IFSC_PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}\b")
DATE_PATTERN = re.compile(
    r"\b(?:\d{1,2}[-/.\s]\d{1,2}[-/.\s]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b"
)
PRICE_PATTERN = re.compile(
    r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?|\b\d{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?\b",
    re.IGNORECASE,
)
WEBSITE_PATTERN = re.compile(r"\b(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b")
LOAN_PATTERN = re.compile(
    r"(?:loan\s*(?:a/c|account|no|number)?[:.\-\s]*)?([A-Z0-9]{6,24})",
    re.IGNORECASE,
)


def extract_regex_hints(text: str) -> RegexExtraction:
    """Extract high-confidence fields using deterministic patterns."""
    normalized = text or ""
    loan_numbers = []
    for match in LOAN_PATTERN.finditer(normalized):
        candidate = match.group(1).strip()
        if any(ch.isdigit() for ch in candidate) and len(candidate) >= 8:
            loan_numbers.append(candidate)

    return RegexExtraction(
        loan_numbers=sorted(set(loan_numbers))[:10],
        ifsc_codes=sorted({item.upper() for item in IFSC_PATTERN.findall(normalized)}),
        dates=sorted(set(DATE_PATTERN.findall(normalized)))[:20],
        prices=sorted(set(PRICE_PATTERN.findall(normalized)))[:20],
        phone_numbers=sorted(set(PHONE_PATTERN.findall(normalized)))[:10],
        websites=sorted(set(WEBSITE_PATTERN.findall(normalized)))[:10],
    )

