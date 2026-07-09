"""Text extraction service for images and PDFs."""

import asyncio
from pathlib import Path

from app.core.exceptions import ProcessingError
from app.core.logger import get_logger
from app.services.ocr.paddle_service import PaddleOCRService
from app.utils.image_utils import is_image_file

logger = get_logger(__name__)


class TextExtractor:
    """Extract text from supported notice files."""

    def __init__(self) -> None:
        self.paddle = PaddleOCRService()

    async def extract(self, path: Path) -> str:
        """Extract OCR/text from an image or PDF."""
        suffix = path.suffix.lower()
        if is_image_file(path):
            return await self.paddle.extract_text(path)
        if suffix == ".pdf":
            return await asyncio.to_thread(self._extract_pdf_text, path)
        raise ProcessingError(f"Unsupported text extraction file type: {suffix}")

    def _extract_pdf_text(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ProcessingError("Install pypdf to extract PDF text") from exc

        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise ProcessingError(
                "PDF has no embedded text. Convert pages to images or use a document OCR service."
            )
        return text

