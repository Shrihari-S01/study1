"""LLM extraction validation and normalization."""

from typing import Any

from app.schemas.extraction import AuctionExtraction, RegexExtraction
from app.services.classifier.asset_classifier import AssetClassifier
from app.services.classifier.auction_classifier import AuctionClassifier
from app.services.classifier.possession_classifier import PossessionClassifier
from app.services.llm.confidence import ConfidenceScorer
from app.utils.currency import normalize_currency
from app.utils.date_utils import normalize_date
from app.utils.helper import clean_text


class ExtractionValidator:
    """Validate, normalize, and enrich LLM output."""

    def __init__(self) -> None:
        self.asset_classifier = AssetClassifier()
        self.auction_classifier = AuctionClassifier()
        self.possession_classifier = PossessionClassifier()
        self.confidence = ConfidenceScorer()

    def validate(
        self,
        llm_json: dict[str, Any],
        regex_hints: RegexExtraction,
        ocr_text: str,
    ) -> AuctionExtraction:
        """Build a normalized extraction from LLM JSON and deterministic hints."""
        normalized = {key: clean_text(str(value)) for key, value in llm_json.items() if value is not None}
        print("="*100)
        print(llm_json)
        print("="*100)
        
        extraction = AuctionExtraction.model_validate(normalized)

        if not extraction.loan_number and regex_hints.loan_numbers:
            extraction.loan_number = regex_hints.loan_numbers[0]
        if not extraction.ifsc and regex_hints.ifsc_codes:
            extraction.ifsc = regex_hints.ifsc_codes[0]
        if not extraction.contact_number and regex_hints.phone_numbers:
            extraction.contact_number = regex_hints.phone_numbers[0]
        if not extraction.website and regex_hints.websites:
            extraction.website = regex_hints.websites[0]

        if not extraction.auction_type:
            extraction.auction_type = self.auction_classifier.classify(ocr_text)
        if not extraction.asset_category or not extraction.movable_immovable:
            asset, movement = self.asset_classifier.classify_asset(f"{ocr_text} {extraction.description}")
            extraction.asset_category = extraction.asset_category or asset
            extraction.movable_immovable = extraction.movable_immovable or movement
        if not extraction.property_type:
            extraction.property_type = extraction.asset_category
        if not extraction.property_category:
            extraction.property_category = extraction.asset_category
        if not extraction.possession_type:
            extraction.possession_type = self.possession_classifier.classify(ocr_text)

        extraction.reserve_price = normalize_currency(extraction.reserve_price)
        extraction.emd = normalize_currency(extraction.emd)
        extraction.demand_notice_date = normalize_date(extraction.demand_notice_date)
        extraction.symbolic_possession_date = normalize_date(extraction.symbolic_possession_date)
        extraction.auction_date = normalize_date(extraction.auction_date)
        extraction.confidence_score = self.confidence.score(extraction)
        return extraction

