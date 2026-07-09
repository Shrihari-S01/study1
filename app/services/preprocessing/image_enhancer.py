"""Image preprocessing pipeline."""

import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.services.preprocessing.image_cleaner import ImageCleaner
from app.utils.image_utils import is_image_file


class ImageEnhancer:
    """Run preprocessing steps before OCR."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.cleaner = ImageCleaner()

    async def enhance(self, input_path: Path) -> Path:
        if not is_image_file(input_path):
            return input_path

        self.settings.processed_dir.mkdir(parents=True, exist_ok=True)

        cleaned_path = (
            self.settings.processed_dir /
            f"{input_path.stem}-cleaned{input_path.suffix}"
        )

        await asyncio.to_thread(
            self.cleaner.clean,
            input_path,
            cleaned_path,
        )

        return cleaned_path