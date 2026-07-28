"""
Processing schemas.

Pydantic schemas used during newspaper processing.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ==========================================================
# Process Request
# ==========================================================

class ProcessRequest(BaseModel):
    """
    Request to start processing.
    """

    upload_id: str = Field(
        ...,
        description="Upload ID of the newspaper.",
    )


# ==========================================================
# Process Status
# ==========================================================

class ProcessStatus(BaseModel):
    """
    Current processing status.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    upload_id: str

    status: str

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    current_step: str = ""

    message: str = ""

    started_at: datetime | None = None

    completed_at: datetime | None = None


# ==========================================================
# Processing Statistics
# ==========================================================

class ProcessingStatistics(BaseModel):
    """
    Processing statistics.
    """

    total_notices: int = 0

    successful_notices: int = 0

    failed_notices: int = 0

    processing_time: float = 0.0

    average_confidence: float = 0.0


# ==========================================================
# Process Result
# ==========================================================

class ProcessResult(BaseModel):
    """
    Final processing result.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    upload_id: str

    status: str

    statistics: ProcessingStatistics


# ==========================================================
# Process Response
# ==========================================================

class ProcessResponse(BaseModel):
    """
    Response after processing.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    upload_id: str

    upload_number: str

    status: str

    total_notices: int

    successful_notices: int

    failed_notices: int

    processing_time: float

    average_confidence: float

    message: str


# ==========================================================
# Process Error
# ==========================================================

class ProcessError(BaseModel):
    """
    Processing error.
    """

    upload_id: str

    status: str = "FAILED"

    error_message: str