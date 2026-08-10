"""
File Manager.

Handles upload file storage operations.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)

settings = get_settings()

class FileManager:
    """
    Handles all file operations.
    """

    def __init__(self) -> None:

        self.original_dir = settings.original_dir

        self.processed_dir = settings.processed_dir

        self.split_dir = settings.split_dir

        self.temp_dir = settings.temp_dir

        self.create_directories()

    def create_directories(
        self,
    ) -> None:
        """
        Create required directories.
        """

        directories = [

            self.original_dir,

            self.processed_dir,

            self.split_dir,

            self.temp_dir,

        ]

        for directory in directories:

            directory.mkdir(

                parents=True,

                exist_ok=True,

            )

        logger.info(
            "Upload directories initialized."
        )

    async def save_file(
        self,
        file: UploadFile,
        filename: str,
    ) -> Path:
        """
        Save uploaded file to original directory.
        """
        target_path = self.original_dir / filename
        try:
            import inspect
            # Seek to start in case of prior reads
            seek_res = file.seek(0)
            if inspect.isgenerator(seek_res) or inspect.isawaitable(seek_res):
                await seek_res

            with open(target_path, "wb") as buffer:
                while True:
                    read_res = file.read(1024 * 1024)  # 1MB chunks
                    if inspect.isgenerator(read_res) or inspect.isawaitable(read_res):
                        chunk = await read_res
                    else:
                        chunk = read_res
                    if not chunk:
                        break
                    buffer.write(chunk)

            logger.info("Saved upload file to: %s", target_path)
            return target_path
        except Exception as exc:
            logger.exception("Failed to write uploaded file to disk.")
            raise exc

    def delete_file(self, file_path: str | Path) -> bool:
        """Safely delete a single file if it exists."""
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            if path.exists() and path.is_file():
                path.unlink()
                logger.debug("Deleted temporary file: %s", path)
                return True
        except Exception as exc:
            logger.warning("Failed to delete file %s: %s", file_path, exc)
        return False

    def cleanup_post_processing(
        self,
        split_paths: list[str | Path] | None = None,
        processed_paths: list[str | Path] | None = None,
        temp_paths: list[str | Path] | None = None,
    ) -> None:
        """
        Execute post-processing file cleanup based on application settings.
        
        Rules:
        - processed/: Deleted if cleanup_after_processing or delete_temp_files is True.
        - temp/: Deleted if cleanup_after_processing or delete_temp_files is True.
        - split/: Deleted if keep_split_images is False AND cleanup_after_processing is True.
        """
        if not (settings.cleanup_after_processing or settings.delete_temp_files):
            return

        # 1. Clean up intermediate processed images (e.g. enhanced, deskewed)
        if processed_paths:
            for p in processed_paths:
                self.delete_file(p)

        # 2. Clean up temp crop/debug files
        if temp_paths:
            for t in temp_paths:
                self.delete_file(t)

        # 3. Clean up split notice images if keep_split_images is False
        if not settings.keep_split_images and split_paths:
            for s in split_paths:
                self.delete_file(s)

        logger.info("Post-processing file cleanup completed.")