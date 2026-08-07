"""
Extraction Validation Service.

Stage 5: Validates AI extracted record dictionaries before mapping and posting to the PHP API.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)


class ExtractionValidationService:
    """
    Validates mandatory fields, numeric integrity, and date formats of extracted auction records.
    """

    @staticmethod
    def validate_record(record: Dict[str, Any], lot_index: int = 1) -> Tuple[bool, List[str]]:
        """
        Validate a single extracted auction record dictionary.

        Returns:
            Tuple[is_valid: bool, list_of_error_messages: List[str]]
        """
        errors: List[str] = []

        # Helper getters checking multiple key synonyms in raw record
        def get_val(*keys) -> str:
            for k in keys:
                val = record.get(k)
                if val is not None:
                    s = str(val).strip()
                    if s and s.lower() not in {"null", "none", "n/a", "undefined"}:
                        return s
            return ""

        # 1. Mandatory Text Fields Validation
        auction_number = get_val("auction_no", "notice_auction_id", "auction_number")
        if not auction_number:
            errors.append(f"Lot #{lot_index}: Missing mandatory field 'auction_number'.")

        seller = get_val("institution_seller", "vendor_name", "seller", "bank_name")
        if not seller:
            errors.append(f"Lot #{lot_index}: Missing mandatory field 'seller' / 'institution_seller'.")

        location = get_val("assets_location", "product_location", "location")
        if not location:
            logger.warning("[Lot #%d] Optional field 'assets_location' missing in AI extraction.", lot_index)

        description = get_val("auction_description", "auction_details", "description")
        if not description and not get_val("asset_type", "asset_category"):
            logger.warning("[Lot #%d] Optional field 'auction_description' missing in AI extraction.", lot_index)

        # 2. Mandatory Financial Fields Validation
        reserve_price_raw = get_val("auction_start_price", "start_floor_price", "reserver_price", "reserve_price")
        if not reserve_price_raw:
            logger.warning("[Lot #%d] Optional field 'reserve_price' / 'auction_start_price' missing in AI extraction.", lot_index)
        else:
            # Clean monetary string
            clean_price = re.sub(r"[^\d.]", "", reserve_price_raw)
            try:
                val = float(clean_price)
                if val < 0:
                    errors.append(f"Lot #{lot_index}: Reserve price cannot be negative ({reserve_price_raw}).")
            except ValueError:
                errors.append(f"Lot #{lot_index}: Non-numeric Reserve price format '{reserve_price_raw}'.")

        # 3. Increment & EMD Price Numeric Checks (if present)
        increment_price_raw = get_val("increment_price")
        if increment_price_raw:
            clean_inc = re.sub(r"[^\d.]", "", increment_price_raw)
            if clean_inc:
                try:
                    float(clean_inc)
                except ValueError:
                    errors.append(f"Lot #{lot_index}: Non-numeric Increment price format '{increment_price_raw}'.")

        emd_price_raw = get_val("emd_amount", "emd_price")
        if emd_price_raw:
            clean_emd = re.sub(r"[^\d.]", "", emd_price_raw)
            if clean_emd:
                try:
                    float(clean_emd)
                except ValueError:
                    errors.append(f"Lot #{lot_index}: Non-numeric EMD amount format '{emd_price_raw}'.")

        # 4. Mandatory Date Fields Validation
        auction_date_raw = get_val("auction_start_datetime", "auction_date")
        if not auction_date_raw:
            errors.append(f"Lot #{lot_index}: Missing mandatory field 'auction_date'.")

        is_valid = len(errors) == 0
        if is_valid:
            logger.info("Extraction validation passed for Lot #%d (auction_number=%s)", lot_index, auction_number)
        else:
            logger.warning("Extraction validation failed for Lot #%d with %d errors: %s", lot_index, len(errors), errors)

        return is_valid, errors
