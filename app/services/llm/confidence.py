"""Confidence scoring for extracted data."""

from app.schemas.extraction import AuctionExtraction

IMPORTANT_FIELDS = (
    "bank_name",
    "borrower_name",
    "auction_type",
    "asset_category",
    "movable_immovable",
    "reserve_price",
    "emd",
    "auction_date",
    "property_address",
    "district",
    "state",
)


class ConfidenceScorer:
    """Compute a simple field-completeness confidence score."""

    def score(self, extraction: AuctionExtraction) -> float:
        values = extraction.model_dump()
        completed = sum(1 for field in IMPORTANT_FIELDS if str(values.get(field) or "").strip())
        return round(completed / len(IMPORTANT_FIELDS), 2)

