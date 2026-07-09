"""OCR service using EasyOCR."""

import asyncio
from pathlib import Path

import easyocr


class PaddleOCRService:
    """OCR wrapper using EasyOCR."""

    def __init__(self):
        self.reader = easyocr.Reader(
            ['en'],
            gpu=False
        )

    async def extract_text(self, image_path: Path) -> str:
        return await asyncio.to_thread(self._extract_sync, image_path)

    def _extract_sync(self, image_path: Path) -> str:
        result = self.reader.readtext(
            str(image_path),
            detail=0
        )

        return "\n".join(result)