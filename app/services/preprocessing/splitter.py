"""Notice splitting placeholder."""

from pathlib import Path


class NoticeSplitter:
    """Detect multiple notices on a page.

    The current implementation returns the full page as one notice. The class is
    intentionally isolated so contour-based or ML-based splitting can be added
    without changing the pipeline contract.
    """

    async def split(self, input_path: Path) -> list[Path]:
        """Return a list of notice image paths."""
        return [input_path]

