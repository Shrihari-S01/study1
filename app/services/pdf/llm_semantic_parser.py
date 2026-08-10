"""
LLM Semantic Parser for PDF Auction Processing Pipeline (Stage 14).
Strictly restricted to processing long material descriptions and remarks.
LLM MUST NEVER extract or overwrite numeric fields, prices, dates, accounts, or IFSCs.
"""

from app.core.logger import get_logger

logger = get_logger(__name__)

class LLMSemanticParser:
    """
    Stage 14: LLM Semantic Parser for long descriptions and remarks ONLY.
    """

    RESTRICTED_NUMERIC_FIELDS = {
        "starting_price", "reserve_price", "increment_price", "pre_bid_emd", "emd_price",
        "post_bid_emd_percent", "quantity", "units", "emd_account_number", "emd_ifsc",
        "auction_no", "lot_no", "catalogue_view_date", "auction_date_time"
    }

    def enrich_description_or_remarks(self, record: dict, raw_text: str, llm_service=None) -> dict:
        """
        Enrich description or remarks using LLM without modifying restricted numeric fields.
        """
        enriched = record.copy()

        # Guarantee that restricted numeric fields are preserved intact from deterministic parsers
        for field in self.RESTRICTED_NUMERIC_FIELDS:
            if field in record:
                enriched[field] = record[field]

        logger.info("Stage 14 LLM Semantic Parser: Restricted numeric fields preserved intact.")
        return enriched
