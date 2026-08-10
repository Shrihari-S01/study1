"""
Pre-PHP Extraction & Mapping Consistency Checker.

Scans raw OCR text against the final mapped PHP payload to detect mapping anomalies:
- Currency amounts present in OCR text but final reserve_price / auction_start_price is 0 or empty.
- Borrower keywords present in OCR text but final borrower_name is empty.
- Raises explicit warnings and alerts before PHP insertion.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)

class PrePHPConsistencyChecker:
    """
    Automated pre-PHP submission consistency verification engine.
    """

    @classmethod
    def check_extraction_consistency(
        cls,
        ocr_text: str,
        final_payload: Dict[str, Any],
        lot_index: int = 1,
    ) -> Tuple[bool, List[str]]:
        """
        Verifies extracted final payload against source OCR text for data loss anomalies.
        """
        warnings: List[str] = []
        if not ocr_text:
            return True, warnings

        ocr_lower = ocr_text.lower()

        # 1. Monetary Value Consistency Check
        has_currency_symbols = any(kw in ocr_lower for kw in ["rs", "inr", "₹", "lakh", "crore", "reserve", "upset", "starting price"])
        has_digits = bool(re.search(r"[\d,]{4,}", ocr_text))

        res_price = str(final_payload.get("reserver_price") or final_payload.get("reserve_price") or final_payload.get("auction_start_price") or "").strip()
        is_price_empty = (not res_price) or res_price in {"0", "0.0", "0.00", "null", "none"}

        if (has_currency_symbols or has_digits) and is_price_empty:
            msg = f"[Lot #{lot_index}] MAPPING INCONSISTENCY WARNING: Raw OCR text contains currency/numeric figures, but final payload reserve_price is empty/0."
            warnings.append(msg)
            logger.warning(msg)

        # 2. Borrower Name Consistency Check
        borrower_keywords = ["borrower", "mortgagor", "applicant", "guarantor", "owner", "loan holder", "proprietor"]
        has_borrower_kw = any(kw in ocr_lower for kw in borrower_keywords)

        borrower_val = str(final_payload.get("borrower_name") or final_payload.get("borrower") or "").strip()
        is_borrower_empty = (not borrower_val) or borrower_val.lower() in {"null", "none", "n/a", "undefined"}

        if has_borrower_kw and is_borrower_empty:
            msg = f"[Lot #{lot_index}] PARSER INCONSISTENCY WARNING: Raw OCR text contains borrower keywords ({[kw for kw in borrower_keywords if kw in ocr_lower]}), but final borrower_name is empty."
            warnings.append(msg)
            logger.warning(msg)

        # 3. Property Location & Description Check
        property_keywords = ["property", "schedule", "flat", "plot", "house", "survey", "land", "address"]
        has_prop_kw = any(kw in ocr_lower for kw in property_keywords)

        loc_val = str(final_payload.get("product_location") or final_payload.get("property_address") or final_payload.get("assets_location") or "").strip()
        is_loc_empty = (not loc_val) or loc_val.lower() in {"null", "none", "n/a", "undefined"}

        if has_prop_kw and is_loc_empty:
            msg = f"[Lot #{lot_index}] LOCATION INCONSISTENCY WARNING: Raw OCR text contains property details, but final product_location is empty."
            warnings.append(msg)
            logger.warning(msg)

        is_consistent = len(warnings) == 0
        return is_consistent, warnings
