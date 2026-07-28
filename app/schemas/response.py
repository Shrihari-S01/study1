"""
Common API response schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Generic Type
# ==========================================================

T = TypeVar("T")


# ==========================================================
# Base API Response
# ==========================================================

class APIResponse(
    BaseModel,
    Generic[T],
):
    """
    Standard API response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    success: bool = True

    message: str = "Success"

    data: T | None = None

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
    )


# ==========================================================
# Error Response
# ==========================================================

class ErrorResponse(BaseModel):
    """
    Error response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    success: bool = False

    message: str

    status_code: int

    errors: list[str] | None = None

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
    )


# ==========================================================
# Pagination
# ==========================================================

class Pagination(BaseModel):
    """
    Pagination information.
    """

    page: int

    page_size: int

    total_records: int

    total_pages: int


# ==========================================================
# Paginated Response
# ==========================================================

class PaginatedResponse(
    BaseModel,
    Generic[T],
):
    """
    Paginated API response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    success: bool = True

    message: str = "Success"

    data: list[T]

    pagination: Pagination

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
    )


# ==========================================================
# Health Response
# ==========================================================

class HealthResponse(BaseModel):
    """
    Health check response.
    """

    status: str

    application: str

    version: str

    database: str

    server_time: datetime = Field(
        default_factory=datetime.utcnow,
    )


# ==========================================================
# Simple Message Response
# ==========================================================

class MessageResponse(BaseModel):
    """
    Simple message response.
    """

    success: bool = True

    message: str