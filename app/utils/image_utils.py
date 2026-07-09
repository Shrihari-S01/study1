"""Image file helpers."""

from pathlib import Path

from app.core.constants import SUPPORTED_IMAGE_EXTENSIONS


def is_image_file(path: str | Path) -> bool:
    """Return true when path extension is an image type."""
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def output_with_suffix(path: Path, suffix: str) -> Path:
    """Build a sibling output path with a suffix before the extension."""
    return path.with_name(f"{path.stem}{suffix}{path.suffix}")

