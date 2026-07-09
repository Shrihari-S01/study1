"""Extraction schemas used between OCR, LLM, and validation."""

from pydantic import BaseModel, ConfigDict, Field


class RegexExtraction(BaseModel):
    """Deterministic hints extracted from OCR text."""

    loan_numbers: list[str] = Field(default_factory=list)
    ifsc_codes: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    prices: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    websites: list[str] = Field(default_factory=list)


class AuctionExtraction(BaseModel):
    """Structured auction extraction returned by Groq and validators."""

    model_config = ConfigDict(populate_by_name=True)

    bank_name: str = ""
    borrower_name: str = ""
    loan_number: str = ""
    auction_type: str = ""
    property_type: str = ""
    property_category: str = ""
    asset_category: str = ""
    movable_immovable: str = ""
    possession_type: str = ""
    reserve_price: str = ""
    emd: str = ""
    demand_notice_date: str = ""
    symbolic_possession_date: str = ""
    auction_date: str = ""
    property_address: str = ""
    district: str = ""
    state: str = ""
    beneficiary_bank: str = ""
    ifsc: str = ""
    contact_person: str = ""
    contact_number: str = ""
    website: str = ""
    description: str = ""
    summary: str = ""
    who: str = ""
    whom: str = ""
    where: str = ""
    when: str = ""
    confidence_score: float = 0.0

