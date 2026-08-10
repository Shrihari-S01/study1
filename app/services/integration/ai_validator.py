"""
AI Schema & Business Validator.

Stage 3: Validates required fields and business rules ONLY on the CommonAISchema.
This module has ZERO knowledge of PHP payload field names.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)

class AISchemaValidator:
    """
    Validates mandatory existence of core AI extraction fields.
    """

    @staticmethod
    def validate_schema(schema: Dict[str, Any], lot_index: int = 1) -> Tuple[bool, List[str]]:
        """
        Validate existence of mandatory AI extraction fields.
        """
        errors: List[str] = []

        def is_empty(val: Any) -> bool:
            if val is None:
                return True
            s = str(val).strip()
            return len(s) == 0 or s.lower() in {"null", "none", "n/a", "undefined"}

        # Critical Fields Check (Must exist to proceed)
        if is_empty(schema.get("auction_number")):
            errors.append(f"Lot #{lot_index}: Missing critical AI field 'auction_number'.")

        if is_empty(schema.get("seller_name")):
            errors.append(f"Lot #{lot_index}: Missing critical AI field 'seller_name'.")

        if is_empty(schema.get("asset_location")) and is_empty(schema.get("description")):
            errors.append(f"Lot #{lot_index}: Missing critical AI field 'asset_location' or 'description'.")

        if is_empty(schema.get("description")) and is_empty(schema.get("asset_type")) and is_empty(schema.get("asset_location")):
            errors.append(f"Lot #{lot_index}: Missing critical AI field 'description', 'asset_type', or 'asset_location'.")

        # Editable fields (auction_start_datetime, reserve_price, etc.) are allowed to be empty/null so users can edit them later in PHP UI.
        is_valid = len(errors) == 0
        logger.info("[%d] AI Schema Validation: valid=%s, critical_errors=%d", lot_index, is_valid, len(errors))
        return is_valid, errors

class AIBusinessValidator:
    """
    Validates domain business rules on AI extraction fields.
    """

    @staticmethod
    def validate_business_rules(schema: Dict[str, Any], lot_index: int = 1) -> Tuple[bool, List[str]]:
        """
        Validate business logic rules:
        - Reserve price non-negative
        - Auction start datetime <= auction end datetime
        """
        errors: List[str] = []

        # 1. Numeric Reserve Price Check
        price_raw = str(schema.get("reserve_price") or "")
        clean_price = re.sub(r"[^\d.]", "", price_raw)
        if clean_price:
            try:
                val = float(clean_price)
                if val < 0:
                    errors.append(f"Lot #{lot_index}: Reserve price cannot be negative ({price_raw}).")
            except ValueError:
                errors.append(f"Lot #{lot_index}: Invalid non-numeric reserve price '{price_raw}'.")

        # 2. Chronological Start <= End Date Rule
        start_val = schema.get("auction_start_datetime")
        end_val = schema.get("auction_end_datetime")

        if start_val and end_val:
            try:
                dt_start = start_val if isinstance(start_val, datetime) else datetime.fromisoformat(str(start_val).replace("Z", ""))
                dt_end = end_val if isinstance(end_val, datetime) else datetime.fromisoformat(str(end_val).replace("Z", ""))
                if dt_end < dt_start:
                    errors.append(f"Lot #{lot_index}: Business Rule Error - End Date ({end_val}) is earlier than Start Date ({start_val}).")
            except Exception:
                pass  # String date formatting will be sanitized in Normalizer

        is_valid = len(errors) == 0
        logger.info("[%d] AI Business Validation: valid=%s, errors=%d", lot_index, is_valid, len(errors))
        return is_valid, errors
