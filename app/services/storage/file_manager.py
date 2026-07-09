"""Async file storage helpers."""

from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.constants import SUPPORTED_UPLOAD_EXTENSIONS
from app.core.exceptions import ValidationError


class FileManager:
    """Safely persist uploaded files."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def save_upload(self, file: UploadFile, listing_id: str) -> Path:
        """Validate and save an uploaded file in chunks."""
        original_name = file.filename or "auction_notice"
        extension = Path(original_name).suffix.lower()
        if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
            raise ValidationError(f"Unsupported file type: {extension}")

        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{listing_id}-{uuid4().hex[:8]}{extension}"
        destination = self.settings.upload_dir / stored_name

        total_size = 0
        async with aiofiles.open(destination, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > self.settings.max_upload_bytes:
                    await out_file.close()
                    destination.unlink(missing_ok=True)
                    raise ValidationError(
                        f"File exceeds {self.settings.MAX_UPLOAD_SIZE_MB} MB upload limit"
                    )
                await out_file.write(chunk)

        await file.seek(0)
        return destination

    async def exists(self, path: str | Path) -> bool:
        """Return whether a file path exists."""
        return Path(path).exists()

