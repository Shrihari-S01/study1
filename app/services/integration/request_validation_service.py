"""
Request Validation Service.

Executes validation on frontend requests:
- validate_file_upload(): File existence, type, size checks for Phase 1 AI Document Extraction.
- validate_master_selections(): Angular master selections validation prior to Phase 3 PHP Insertion.
- validate_request(): Combined validation helper for file and master selections.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from fastapi import UploadFile
from app.schemas.integration_schemas import IntegrationMasterData
from app.core.logger import get_logger

logger = get_logger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class RequestValidationService:
    """
    Decoupled request validation separating file checks from Angular master selections.
    """

    @staticmethod
    def validate_file_upload(
        file: UploadFile,
        content_bytes: bytes,
    ) -> Tuple[bool, str]:
        """
        Validate file upload constraints for Phase 1 AI Extraction.
        Does NOT inspect or require Angular master selections.
        """
        if not file or not file.filename:
            return False, "No uploaded file provided."
        if not content_bytes or len(content_bytes) == 0:
            return False, f"Uploaded file '{file.filename}' is empty (0 bytes)."
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            return False, f"File size ({len(content_bytes)} bytes) exceeds max limit of {MAX_FILE_SIZE_BYTES} bytes."

        filename_lower = file.filename.lower()
        is_image = any(filename_lower.endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS)
        is_pdf = any(filename_lower.endswith(ext) for ext in ALLOWED_PDF_EXTENSIONS)
        if not is_image and not is_pdf:
            return False, f"Unsupported file type for '{file.filename}'. Must be Image or PDF."

        return True, "File upload validation passed."

    @staticmethod
    def validate_master_selections(
        master_data: IntegrationMasterData,
    ) -> Tuple[bool, List[str], str]:
        """
        Validate Angular master selections required for Phase 3 PHP Insertion.
        Called ONLY immediately before PHP insertion.
        """
        missing_fields: List[str] = []

        def is_blank(val: Any) -> bool:
            if val is None:
                return True
            s = str(val).strip()
            return len(s) == 0 or s.lower() in {"null", "none", "undefined"}

        if is_blank(master_data.vendor_id):
            missing_fields.append("vendor_id")
        if is_blank(master_data.section_id):
            missing_fields.append("section_id")
        if is_blank(master_data.part_id):
            missing_fields.append("part_id")
        if is_blank(master_data.auction_type):
            missing_fields.append("auction_type")
        if is_blank(master_data.payment_type):
            missing_fields.append("payment_type")

        is_valid = len(missing_fields) == 0
        msg = f"Missing required Angular master selections: {', '.join(missing_fields)}" if missing_fields else "Master selections validation passed."

        if not is_valid:
            logger.warning("Master Selection Validation Failed: missing_fields=%s", missing_fields)
        else:
            logger.info("Master Selection Validation Passed: vendor_id='%s'", master_data.vendor_id)

        return is_valid, missing_fields, msg

    @classmethod
    def validate_request(
        cls,
        file: UploadFile,
        content_bytes: bytes,
        master_data: IntegrationMasterData,
    ) -> Tuple[bool, List[str], str]:
        """
        Combined validation for file upload and master selections.
        """
        file_valid, file_msg = cls.validate_file_upload(file, content_bytes)
        if not file_valid:
            return False, [], file_msg

        master_valid, missing, master_msg = cls.validate_master_selections(master_data)
        if not master_valid:
            return False, missing, master_msg

        return True, [], "Request validation passed."
