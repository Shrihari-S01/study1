"""Auction API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuctionRead(BaseModel):
    """Auction data returned by API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    upload_id: str
    listing_id: str
    bank_name: str | None = None
    borrower_name: str | None = None
    loan_number: str | None = None
    auction_type: str | None = None
    property_type: str | None = None
    property_category: str | None = None
    asset_category: str | None = None
    movable_immovable: str | None = None
    possession_type: str | None = None
    reserve_price: str | None = None
    emd: str | None = None
    demand_notice_date: str | None = None
    symbolic_possession_date: str | None = None
    auction_date: str | None = None
    property_address: str | None = None
    district: str | None = None
    state: str | None = None
    beneficiary_bank: str | None = None
    ifsc: str | None = None
    contact_person: str | None = None
    contact_number: str | None = None
    website: str | None = None
    description: str | None = None
    summary: str | None = None
    who: str | None = None
    whom: str | None = None
    where_location: str | None = None
    when_details: str | None = None
    confidence_score: float
    word_path: str | None = None
    excel_path: str | None = None
    created_at: datetime
    updated_at: datetime


class AuctionProcessResponse(BaseModel):
    """Processing response."""

    upload_id: str
    auction: AuctionRead
    word_download_url: str
    excel_download_url: str

