"""
Auction database model.

Stores extracted auction details from newspaper sale notices.
One uploaded newspaper may contain multiple auction notices.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.upload import Upload

class Auction(
    Base,
    TimestampMixin,
):
    """
    Auction information extracted from newspaper.
    """

    __tablename__ = "auctions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    upload_id: Mapped[str] = mapped_column(
        ForeignKey(
            "uploads.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    upload: Mapped["Upload"] = relationship(
        "Upload",
        back_populates="auctions",
    )

    asset_type: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    asset_category: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    auction_no: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    auction_description: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    auction_type: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    assets_location: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    borrower: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    auction_start_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    increment_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    currency: Mapped[str] = mapped_column(
        String(20),
        default="INR",
    )

    auction_start_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    auction_end_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    auction_live_status: Mapped[str] = mapped_column(
        String(50),
        default="Pending",
    )

    auto_extension: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    auto_extension_mode: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    auction_extend_time: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    first_bid_acceptance_condition: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    inspection_from_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    inspection_to_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    submit_application: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    emd_bank_name: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    emd_account_no: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    emd_ifsc: Mapped[str] = mapped_column(
        String(20),
        default="",
    )

    emd_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    authorized_officer_name: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    authorized_officer_number: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    payment_type: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    remarks: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        default=0.0,
    )

    possession_type: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    asset_id: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    notice_auction_id: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    institution_seller: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    auction_office: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    auction_department: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    digital_certificate: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    catalogue_view_date: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    asset_subcategory: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    full_payment_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    delivery_of_material_taken: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    quantity: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    units: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    start_floor_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    vendor_name: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    sum_of_carat_18: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    sum_of_carat_19: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    sum_of_carat_20: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    sum_of_carat_21: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    sum_of_carat_22: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    sum_of_carat_23: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    sum_of_carat_24: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    sum_of_net_weight_total: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    sum_of_gross_weight_total: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    year: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    reg_no: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    repo_date: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    km_driven: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    rc: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    chassis_number: Mapped[str] = mapped_column(
        String(100),
        default="",
    )

    yard_rent_percent: Mapped[str] = mapped_column(
        String(50),
        default="",
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        default="",
    )
