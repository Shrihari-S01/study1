"""Small reusable helpers."""

from datetime import UTC, datetime
from uuid import uuid4

from app.core.constants import LISTING_ID_PREFIX


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def generate_listing_id() -> str:
    """Generate a unique listing id suitable for external reference."""
    today = utc_now().strftime("%Y%m%d")
    suffix = uuid4().hex[:8].upper()
    return f"{LISTING_ID_PREFIX}-{today}-{suffix}"


def clean_text(value: str | None) -> str:
    """Normalize whitespace while preserving readable text."""
    if not value:
        return ""
    return " ".join(value.replace("\x00", " ").split())

