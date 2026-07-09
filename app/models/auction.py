"""Auction database model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

from typing import List

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.upload import Upload


class Auction(Base):
    """Final validated auction notice data."""

    __tablename__ = "auctions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    upload_id: Mapped[str] = mapped_column(String(36), ForeignKey("uploads.id"), index=True)
    listing_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    borrower_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    loan_number: Mapped[str | None] = mapped_column(String(128), nullable=True)

    auction_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    property_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    asset_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    movable_immovable: Mapped[str | None] = mapped_column(String(64), nullable=True)
    possession_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    reserve_price: Mapped[str | None] = mapped_column(String(128), nullable=True)
    emd: Mapped[str | None] = mapped_column(String(128), nullable=True)
    demand_notice_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    symbolic_possession_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auction_date: Mapped[str | None] = mapped_column(String(64), nullable=True)

    property_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)

    beneficiary_bank: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ifsc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    who: Mapped[str | None] = mapped_column(Text, nullable=True)
    whom: Mapped[str | None] = mapped_column(Text, nullable=True)
    where_location: Mapped[str | None] = mapped_column("where_location", Text, nullable=True)
    when_details: Mapped[str | None] = mapped_column("when_details", Text, nullable=True)

    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    regex_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    llm_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    word_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    excel_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # upload = relationship("Upload", back_populates="auctions")
    
    upload: Mapped["Upload"] = relationship(
    "Upload",
    back_populates="auctions",
) 

