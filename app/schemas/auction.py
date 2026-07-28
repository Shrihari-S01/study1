"""
Auction schemas.

Pydantic schemas for Auction CRUD operations.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Base Schema
# ==========================================================

class AuctionBase(BaseModel):
    """
    Common auction fields.
    """

    # ------------------------------------------------------
    # Asset Details
    # ------------------------------------------------------

    asset_type: str = Field(
        default="",
        max_length=100,
    )

    asset_category: str = Field(
        default="",
        max_length=100,
    )

    auction_no: str = Field(
        default="",
        max_length=100,
    )

    auction_description: str = Field(
        default="",
    )

    auction_type: str = Field(
        default="",
        max_length=100,
    )

    assets_location: str = Field(
        default="",
    )

    borrower: str = Field(
        default="",
    )

# ==========================================================
# Auction Price Details
# ==========================================================

    auction_start_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    increment_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    currency: str = Field(
        default="INR",
        max_length=20,
    )

    # ------------------------------------------------------
    # Auction Schedule
    # ------------------------------------------------------

    auction_start_datetime: Optional[datetime] = None

    auction_end_datetime: Optional[datetime] = None

    auction_live_status: str = Field(
        default="Pending",
        max_length=50,
    )

    # ------------------------------------------------------
    # Auto Extension
    # ------------------------------------------------------

    auto_extension: bool = False

    auto_extension_mode: str = Field(
        default="",
        max_length=50,
    )

    auction_extend_time: int = Field(
        default=0,
        ge=0,
    )

    first_bid_acceptance_condition: str = Field(
        default="",
        max_length=255,
    )

    # ======================================================
    # Inspection Schedule
    # ======================================================

    inspection_from_date: Optional[date] = None

    inspection_to_date: Optional[date] = None

    submit_application: str = Field(
        default="",
        max_length=255,
    )

    # ======================================================
    # EMD Details
    # ======================================================

    emd_bank_name: str = Field(
        default="",
        max_length=255,
    )

    emd_account_no: str = Field(
        default="",
        max_length=100,
    )

    emd_ifsc: str = Field(
        default="",
        max_length=20,
    )

    emd_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    # ======================================================
    # Authorized Officer
    # ======================================================

    authorized_officer_name: str = Field(
        default="",
        max_length=255,
    )

    authorized_officer_number: str = Field(
        default="",
        max_length=30,
    )

    # ------------------------------------------------------
    # Payment and Interest Fields
    # ------------------------------------------------------

    payment_type: str = Field(
        default="",
    )

    are_you_interested: str = Field(
        default="",
    )

    # ======================================================
    # Additional Information
    # ======================================================

    remarks: str = Field(
        default="",
    )

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

# ==========================================================
# Create Schema
# ==========================================================

class AuctionCreate(AuctionBase):
    """
    Schema used for creating a new auction.
    """

    upload_id: str = Field(
        ...,
        description="Upload ID associated with this auction.",
    )


# ==========================================================
# Update Schema
# ==========================================================

class AuctionUpdate(BaseModel):
    """
    Schema used for updating auction details.

    Every field is optional.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    asset_type: Optional[str] = None

    asset_category: Optional[str] = None

    auction_no: Optional[str] = None

    auction_description: Optional[str] = None

    auction_type: Optional[str] = None

    assets_location: Optional[str] = None

    borrower: Optional[str] = None

    auction_start_price: Optional[Decimal] = None

    increment_price: Optional[Decimal] = None

    currency: Optional[str] = None

    auction_start_datetime: Optional[datetime] = None

    auction_end_datetime: Optional[datetime] = None

    auction_live_status: Optional[str] = None

    auto_extension: Optional[bool] = None

    auto_extension_mode: Optional[str] = None

    auction_extend_time: Optional[int] = None

    first_bid_acceptance_condition: Optional[str] = None

    inspection_from_date: Optional[date] = None

    inspection_to_date: Optional[date] = None

    submit_application: Optional[str] = None

    emd_bank_name: Optional[str] = None

    emd_account_no: Optional[str] = None

    emd_ifsc: Optional[str] = None

    emd_amount: Optional[Decimal] = None

    authorized_officer_name: Optional[str] = None

    authorized_officer_number: Optional[str] = None

    payment_type: Optional[str] = None

    are_you_interested: Optional[str] = None

    remarks: Optional[str] = None

    confidence_score: Optional[float] = None

# ==========================================================
# Response Schema
# ==========================================================

class AuctionResponse(AuctionBase):
    """
    Response schema returned to the frontend.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    upload_id: str

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Auction Summary
# ==========================================================

class AuctionSummary(BaseModel):
    """
    Lightweight auction information.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    auction_no: str

    borrower: str

    asset_type: str

    auction_start_price: Decimal

    currency: str

    auction_start_datetime: Optional[datetime]

    auction_live_status: str

    confidence_score: float


# ==========================================================
# Auction List Response
# ==========================================================

class AuctionListResponse(BaseModel):
    """
    List of auctions.
    """

    total_records: int

    auctions: list[AuctionResponse]


# ==========================================================
# Auction Processing Response
# ==========================================================

class AuctionProcessResponse(BaseModel):
    """
    Returned after processing one uploaded newspaper.
    """

    upload_id: str

    total_notices: int

    successful_notices: int

    failed_notices: int

    processing_time: float

    average_confidence: float

    auctions: list[AuctionResponse]


# ==========================================================
# Auction Delete Response
# ==========================================================

class AuctionDeleteResponse(BaseModel):
    """
    Delete response.
    """

    success: bool

    message: str


# ==========================================================
# Auction Search Response
# ==========================================================

class AuctionSearchResponse(BaseModel):
    """
    Search response.
    """

    keyword: str

    total_records: int

    auctions: list[AuctionResponse]