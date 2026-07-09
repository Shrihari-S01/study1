"""Shared application constants."""

from enum import StrEnum


class UploadStatus(StrEnum):
    """Lifecycle states for an uploaded auction notice."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


SUPPORTED_UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf"}
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
SUPPORTED_DOWNLOAD_TYPES = {"word", "excel"}

DEFAULT_MAX_UPLOAD_MB = 25
LISTING_ID_PREFIX = "AUC"

