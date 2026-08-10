"""
Upload Service.

Handles newspaper upload operations.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.constants import (
    SUPPORTED_EXTENSIONS,
    UPLOAD_UPLOADED,
)
from app.core.exceptions import (
    InvalidFileException,
    FileStorageException,
    RecordNotFoundException,
)
from app.core.logger import get_logger

from app.models.upload import Upload

from app.repositories.upload_repository import (
    UploadRepository,
)

from app.services.upload.file_manager import (
    FileManager,
)

logger = get_logger(__name__)

settings = get_settings()

class UploadService:
    """
    Upload service.
    """

    def __init__(
        self,
        repository: UploadRepository,
    ) -> None:

        self.repository = repository

        self.file_manager = FileManager()

    async def upload_file(
        self,
        file: UploadFile,
    ) -> Upload:
        """
        Upload and store newspaper file.

        Parameters
        ----------
        file : UploadFile

        Returns
        -------
        Upload
        """

        logger.info(
            "Uploading file: %s",
            file.filename,
        )

        # ------------------------------------------------------
        # Validate filename
        # ------------------------------------------------------

        if not file.filename:

            raise InvalidFileException(
                "Filename is missing."
            )

        extension = Path(
            file.filename,
        ).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:

            raise InvalidFileException(

                f"Unsupported file type: {extension}"

            )

        # ------------------------------------------------------
        # Generate Upload Number
        # ------------------------------------------------------

        upload_number = self.generate_upload_number()

        stored_filename = (
            upload_number + extension
        )

        # ------------------------------------------------------
        # Save File
        # ------------------------------------------------------

        try:

            saved_path = await self.file_manager.save_file(

                file=file,

                filename=stored_filename,

            )

        except Exception as exc:

            logger.exception(
                "Unable to save uploaded file."
            )

            raise FileStorageException(
                str(exc),
            ) from exc

        # ------------------------------------------------------
        # File Information
        # ------------------------------------------------------

        file_size = saved_path.stat().st_size

        content_type = (

            file.content_type

            or

            mimetypes.guess_type(
                saved_path.name,
            )[0]

            or

            "application/octet-stream"

        )

        # ------------------------------------------------------
        # Create Upload Model
        # ------------------------------------------------------

        upload = Upload(

            upload_number=upload_number,

            original_filename=file.filename,

            stored_filename=stored_filename,

            file_extension=extension,

            content_type=content_type,

            file_size=file_size,

            original_file_path=str(saved_path),

            processed_file_path="",

            split_folder_path="",

            status=UPLOAD_UPLOADED,

            total_notices=0,

            successful_notices=0,

            failed_notices=0,

            processing_time=0.0,

            confidence_score=0.0,

            error_message="",

        )

        upload = await self.repository.create(
            upload,
        )

        logger.info(

            "Upload completed successfully: %s",

            upload.upload_number,

        )

        return upload
    

    async def get_upload(
        self,
        upload_id: str,
    ) -> Upload:
        """
        Return upload by ID.

        Parameters
        ----------
        upload_id : str

        Returns
        -------
        Upload
        """

        upload = await self.repository.get_by_id(
            upload_id,
        )

        if upload is None:

            logger.warning(
                "Upload not found: %s",
                upload_id,
            )

            raise RecordNotFoundException(
                "Upload not found."
            )

        return upload

    async def get_upload_by_number(
        self,
        upload_number: str,
    ) -> Upload:
        """
        Return upload using upload number.

        Parameters
        ----------
        upload_number : str

        Returns
        -------
        Upload
        """

        upload = await self.repository.get_by_upload_number(
            upload_number,
        )

        if upload is None:

            logger.warning(
                "Upload not found: %s",
                upload_number,
            )

            raise RecordNotFoundException(
                "Upload not found."
            )

        return upload

    async def get_all_uploads(
        self,
        limit: int = 100,
    ) -> list[Upload]:
        """
        Return all uploaded files.

        Parameters
        ----------
        limit : int

        Returns
        -------
        list[Upload]
        """

        uploads = await self.repository.get_all(
            limit=limit,
        )

        logger.info(
            "Retrieved %d uploads.",
            len(uploads),
        )

        return uploads

    async def exists(
        self,
        upload_id: str,
    ) -> bool:
        """
        Check upload existence.

        Parameters
        ----------
        upload_id : str

        Returns
        -------
        bool
        """

        return await self.repository.exists(
            upload_id,
        )
    

    async def update_status(
        self,
        upload_id: str,
        status: str,
        error_message: str = "",
    ) -> Upload:
        """
        Update upload processing status.

        Parameters
        ----------
        upload_id : str

        status : str

        error_message : str

        Returns
        -------
        Upload
        """

        upload = await self.get_upload(
            upload_id,
        )

        upload = await self.repository.update_status(

            upload=upload,

            status=status,

            error_message=error_message,

        )

        logger.info(

            "Upload %s status updated to %s",

            upload.upload_number,

            status,

        )

        return upload

    async def update_statistics(
        self,
        upload_id: str,
        total_notices: int,
        successful_notices: int,
        failed_notices: int,
        processing_time: float,
        confidence_score: float,
    ) -> Upload:
        """
        Update upload processing statistics.

        Parameters
        ----------
        upload_id : str

        total_notices : int

        successful_notices : int

        failed_notices : int

        processing_time : float

        confidence_score : float

        Returns
        -------
        Upload
        """

        upload = await self.get_upload(
            upload_id,
        )

        upload = await self.repository.update_statistics(

            upload=upload,

            total_notices=total_notices,

            successful_notices=successful_notices,

            failed_notices=failed_notices,

            processing_time=processing_time,

            confidence_score=confidence_score,

        )

        logger.info(

            "Statistics updated for upload %s",

            upload.upload_number,

        )

        return upload

    async def mark_completed(
        self,
        upload_id: str,
        total_notices: int,
        successful_notices: int,
        failed_notices: int,
        processing_time: float,
        confidence_score: float,
    ) -> Upload:
        """
        Mark upload as completed.
        """

        upload = await self.update_statistics(

            upload_id=upload_id,

            total_notices=total_notices,

            successful_notices=successful_notices,

            failed_notices=failed_notices,

            processing_time=processing_time,

            confidence_score=confidence_score,

        )

        upload = await self.repository.update_status(

            upload=upload,

            status="COMPLETED",

            error_message="",

        )

        logger.info(

            "Upload %s completed successfully.",

            upload.upload_number,

        )

        return upload

    async def mark_failed(
        self,
        upload_id: str,
        error_message: str,
    ) -> Upload:
        """
        Mark upload as failed.
        """

        upload = await self.get_upload(
            upload_id,
        )

        upload = await self.repository.update_status(

            upload=upload,

            status="FAILED",

            error_message=error_message,

        )

        logger.error(

            "Upload %s failed : %s",

            upload.upload_number,

            error_message,

        )

        return upload
    

    async def delete_upload(
        self,
        upload_id: str,
    ) -> None:
        """
        Delete upload and its files.
        """

        upload = await self.get_upload(
            upload_id,
        )

        # Delete original file
        if upload.original_file_path:

            self.file_manager.delete_file(

                Path(upload.original_file_path),

            )

        # Delete processed file
        if upload.processed_file_path:

            self.file_manager.delete_file(

                Path(upload.processed_file_path),

            )

        # Delete split folder
        if upload.split_folder_path:

            self.file_manager.delete_directory(

                Path(upload.split_folder_path),

            )

        await self.repository.delete(
            upload,
        )

        logger.info(
            "Upload deleted successfully : %s",
            upload.upload_number,
        )

    def generate_upload_number(
        self,
    ) -> str:
        """
        Generate unique upload number.
        """

        return f"UPL-{uuid4().hex[:8].upper()}"

    def validate_extension(
        self,
        extension: str,
    ) -> bool:
        """
        Validate file extension.
        """

        return extension.lower() in SUPPORTED_EXTENSIONS

    def validate_file_size(
        self,
        file_size: int,
    ) -> bool:
        """
        Validate upload size.
        """

        return file_size <= settings.max_upload_size

    async def get_status(
        self,
        upload_id: str,
    ) -> str:
        """
        Return upload status.
        """

        upload = await self.get_upload(
            upload_id,
        )

        return upload.status

    async def count_uploads(
        self,
    ) -> int:
        """
        Return total uploads.
        """

        return await self.repository.count()

    async def is_ready(
        self,
    ) -> bool:
        """
        Check upload service.
        """

        try:

            await self.repository.count()

            return True

        except Exception:

            logger.exception(
                "UploadService health check failed."
            )

            return False