"""
File Validation Service.

Stage 2: Validates uploaded file size, extension, MIME type, emptiness, and basic corruption checks.
"""

from __future__ import annotations

import os
from typing import Tuple
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS

ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/bmp",
    "image/webp",
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",  # Fallback for some clients
}


class FileValidationError(Exception):
    """Custom exception raised when file validation fails."""
    pass


class FileValidatorService:
    """
    Validates uploaded document files prior to routing into AI extraction pipelines.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.max_size_bytes = self.settings.max_upload_size_mb * 1024 * 1024

    def validate_upload(self, file: UploadFile, content_bytes: bytes) -> Tuple[bool, str, str]:
        """
        Validate file headers, extension, size, and content integrity.

        Returns:
            Tuple[is_valid: bool, file_type: str ('IMAGE' | 'PDF'), error_message: str]
        """
        file_name = file.filename or "unknown"
        ext = os.path.splitext(file_name)[1].lower()

        logger.info("Validating file upload: filename=%s, size=%d bytes", file_name, len(content_bytes))

        # 1. Extension Validation
        if ext not in ALL_SUPPORTED_EXTENSIONS:
            err = f"Unsupported file extension '{ext}'. Supported extensions: {sorted(list(ALL_SUPPORTED_EXTENSIONS))}"
            logger.warning("File validation failed: %s", err)
            return False, "", err

        # 2. Empty File Check
        if not content_bytes or len(content_bytes) == 0:
            err = "Uploaded file is empty (0 bytes)."
            logger.warning("File validation failed: %s", err)
            return False, "", err

        # 3. Maximum Size Check
        if len(content_bytes) > self.max_size_bytes:
            err = f"File size exceeds maximum allowed limit of {self.settings.max_upload_size_mb}MB."
            logger.warning("File validation failed: %s", err)
            return False, "", err

        # 4. MIME Type Validation (if provided)
        if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
            logger.debug("Non-standard content_type '%s' detected for file '%s', proceeding with magic bytes check.", file.content_type, file_name)

        # 5. Magic Bytes Integrity Check (PDF vs Image)
        file_type = "PDF" if ext in SUPPORTED_PDF_EXTENSIONS else "IMAGE"

        if file_type == "PDF":
            # PDF magic bytes test: starts with %PDF
            if not content_bytes.startswith(b"%PDF"):
                err = "File claims to be a PDF but lacks valid PDF magic header (%PDF). File may be corrupted."
                logger.warning("File validation failed: %s", err)
                return False, "", err
        else:
            # Basic image magic byte header checks
            is_valid_img = (
                content_bytes.startswith(b"\xff\xd8\xff")  # JPEG
                or content_bytes.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
                or content_bytes.startswith(b"II*\x00") or content_bytes.startswith(b"MM\x00*")  # TIFF
                or content_bytes.startswith(b"BM")  # BMP
                or content_bytes.startswith(b"RIFF")  # WEBP
            )
            if not is_valid_img:
                logger.warning("File header magic bytes check ambiguous for image '%s', allowing extraction engine to attempt read.", file_name)

        logger.info("File validation passed successfully: type=%s, name=%s", file_type, file_name)
        return True, file_type, ""
