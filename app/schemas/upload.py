"""
Upload schemas.

Pydantic schemas for Upload operations.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ==========================================================
# Upload Base
# ==========================================================

class UploadBase(BaseModel):
    """
    Common upload fields.
    """

    original_filename: str = Field(
        ...,
        max_length=255,
    )

    stored_filename: str = Field(
        ...,
        max_length=255,
    )

    file_extension: str = Field(
        ...,
        max_length=20,
    )

    content_type: str = Field(
        ...,
        max_length=100,
    )

    file_size: int = Field(
        ...,
        ge=0,
    )

    original_file_path: str

    processed_file_path: str = ""

    split_folder_path: str = ""

    status: str = "UPLOADED"

    total_notices: int = 0

    successful_notices: int = 0

    failed_notices: int = 0

    processing_time: float = 0.0

    confidence_score: float = 0.0

    error_message: str = ""


# ==========================================================
# Upload Create
# ==========================================================

class UploadCreate(UploadBase):
    """
    Schema for creating upload.
    """

    upload_number: str


# ==========================================================
# Upload Update
# ==========================================================

class UploadUpdate(BaseModel):
    """
    Schema for updating upload.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    processed_file_path: str | None = None

    split_folder_path: str | None = None

    status: str | None = None

    total_notices: int | None = None

    successful_notices: int | None = None

    failed_notices: int | None = None

    processing_time: float | None = None

    confidence_score: float | None = None

    error_message: str | None = None


# ==========================================================
# Upload Response
# ==========================================================

class UploadResponse(UploadBase):
    """
    Upload response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    upload_number: str

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Upload Summary
# ==========================================================

class UploadSummary(BaseModel):
    """
    Upload summary.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    upload_number: str

    original_filename: str

    status: str

    total_notices: int

    processing_time: float

    confidence_score: float

    created_at: datetime


# ==========================================================
# Upload List Response
# ==========================================================

class UploadListResponse(BaseModel):
    """
    Upload list response.
    """

    total_records: int

    uploads: list[UploadResponse]


# ==========================================================
# Upload Processing Response
# ==========================================================

class UploadProcessResponse(BaseModel):
    """
    Returned after upload processing.
    """

    upload_id: str

    upload_number: str

    status: str

    total_notices: int

    successful_notices: int

    failed_notices: int

    processing_time: float

    confidence_score: float


# ==========================================================
# Upload Delete Response
# ==========================================================

class UploadDeleteResponse(BaseModel):
    """
    Delete response.
    """

    success: bool

    message: str