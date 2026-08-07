"""
Auction Processing Session Model.

Database table storing stateful Phase 1 document extraction sessions, extracted JSON payloads,
consistency reports, workflow status, and Phase 2 PHP submission results.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class AuctionProcessingSession(Base, TimestampMixin):
    """
    Persistent stateful processing session model for 2-phase integration.
    """

    __tablename__ = "auction_processing_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    processing_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="UPLOADED",
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        default="",
        nullable=False,
    )

    document_type: Mapped[str] = mapped_column(
        String(32),
        default="PDF",
        nullable=False,
    )

    extracted_json: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )

    canonical_json: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )

    mapped_payload: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )

    consistency_report: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )

    php_record_id: Mapped[str] = mapped_column(
        String(64),
        default="",
        nullable=False,
    )

    php_response_message: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    error_detail: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(days=7),
        nullable=False,
    )
