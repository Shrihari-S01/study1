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

    # ==========================================================
    # Create Directories
    # ==========================================================

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

    # ==========================================================
    # Save File
    # ==========================================================

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