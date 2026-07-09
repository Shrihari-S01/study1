"""Date parsing utilities."""

from datetime import datetime

DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d %B %Y", "%d %b %Y")


def normalize_date(value: str | None) -> str:
    """Return a date as DD-MM-YYYY when parsing succeeds."""
    if not value:
        return ""
    cleaned = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return cleaned

