"""
Upload database model.

Stores uploaded newspaper image information.
One upload may contain multiple auction notices.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Float,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import (
    Base,
    TimestampMixin,
)

if TYPE_CHECKING:
    from app.models.auction import Auction

class Upload(
    Base,
    TimestampMixin,
):
    """
    Uploaded newspaper file.
    """

    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    upload_number: Mapped[str] = mapped_column(
    String(100),
    unique=True,
    nullable=False,
    index=True,
    default=lambda: f"UPL-{uuid4().hex[:10].upper()}",
)

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_extension: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    original_file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    processed_file_path: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    split_folder_path: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="UPLOADED",
        index=True,
    )

    total_notices: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    successful_notices: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    failed_notices: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    processing_time: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    confidence_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    auctions: Mapped[list["Auction"]] = relationship(
        "Auction",
        back_populates="upload",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(
        self,
    ) -> str:

        return (
            f"<Upload("
            f"id='{self.id}', "
            f"upload_number='{self.upload_number}', "
            f"status='{self.status}'"
            f")>"
        )