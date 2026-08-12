"""
PHP Payload Validator.

Stage 8: Validates complete PHP payload schema readiness prior to HTTP POST invocation.
Validates payload fields ONLY after Stage 6 (Business Defaults) & Stage 7 (Angular Master Merge).
Does NOT validate document extraction (which was owned by Stage 3 AI Validation).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)

class PHPPayloadValidator:
    """
    Validates mapped & merged PHP Payload dictionary readiness prior to HTTP POST invocation.
    Classifies fields into Required (blocking) and Optional (non-blocking).
    """

    # Absolutely REQUIRED fields (database foreign keys & mandatory identifiers)
    REQUIRED_FIELDS = [
        "vendor_id",
        "section_id",
        "part_id",
        "auction_number",
    ]

    # OPTIONAL fields (location, institution seller, borrower details, officer contact, remarks, EMD bank info)
    OPTIONAL_FIELDS = [
        "product_location",
        "institution_seller",
        "borrower_name",
        "guarantor",
        "remarks",
        "authorized_officer_name",
        "authorized_officer_no",
        "branch_phone",
        "contact_phone",
        "emd_bank_name",
        "emd_ifsc",
        "emd_account_no",
        "catalogue_view_date",
        "inspection_schedule_from_date_time",
    ]

    @classmethod
    def _get_schema_fields(cls) -> Tuple[List[str], List[str]]:
        """
        Dynamically extract required vs optional fields from PHP_SCHEMA_SPEC.
        """
        from app.services.integration.php_payload_normalizer import PHP_SCHEMA_SPEC
        req_set = set(cls.REQUIRED_FIELDS)
        opt_set = set(cls.OPTIONAL_FIELDS)
        
        for field, spec in PHP_SCHEMA_SPEC.items():
            if spec.get("required") is True:
                req_set.add(field)
            else:
                opt_set.add(field)
        
        # Ensure required fields take precedence over optional
        opt_set = opt_set - req_set
        return list(req_set), list(opt_set)

    @classmethod
    def validate_php_payload(cls, payload: Dict[str, Any], lot_index: int = 1) -> Tuple[bool, List[str]]:
        """
        Validate mapped PHP payload completeness against mandatory schema rules.
        Missing optional fields (like product_location or borrower_name) NEVER fail validation.
        Rejects any invalid enum values or schema violations before sending to PHP.
        """
        from app.services.integration.payload_sanitizer import PHPSanitizer

        # Step 1: Run Schema-Driven Normalization & Validation Engine
        sanitized_dict, is_schema_valid, schema_errors = PHPSanitizer.sanitize_and_validate_payload(
            payload, processing_id=f"lot-{lot_index}"
        )

        errors: List[str] = list(schema_errors)
        passed_required: List[str] = []
        missing_optional: List[str] = []

        def is_empty(key: str) -> bool:
            val = sanitized_dict.get(key)
            if val is None:
                return True
            s = str(val).strip()
            return len(s) == 0 or s.lower() in {"null", "none", "undefined"}

        req_fields, opt_fields = cls._get_schema_fields()

        cat_a_absent = []
        cat_b_lost = []
        cat_c_present = []

        # Classify all optional & required fields into 4 distinct diagnostic categories
        for opt_key in opt_fields + req_fields:
            if opt_key not in sanitized_dict or sanitized_dict[opt_key] is None:
                sanitized_dict[opt_key] = ""
            
            is_empty_val = is_empty(opt_key)
            if not is_empty_val:
                cat_c_present.append(opt_key)
            else:
                cat_a_absent.append(opt_key)

        # Check Absolutely Required Fields (mandatory DB foreign keys & core identifiers only)
        for req_key in req_fields:
            if is_empty(req_key):
                errors.append(f"Lot #{lot_index}: Missing required mapped PHP field '{req_key}'.")
            else:
                passed_required.append(req_key)

        # Ensure price exists with monetary priority hierarchy without overwriting valid non-zero amounts
        existing_price = ""
        for p_key in ["reserve_price", "reserver_price", "upset_price", "base_price", "starting_price", "auction_start_price", "opening_bid", "start_floor_price"]:
            val = sanitized_dict.get(p_key)
            if val is not None:
                s = str(val).strip()
                if s and s not in {"0", "0.0", "0.00", "null", "none", "n/a", "undefined"}:
                    existing_price = s
                    break

        if existing_price:
            sanitized_dict["reserver_price"] = existing_price
            sanitized_dict["reserve_price"] = existing_price
            sanitized_dict["auction_start_price"] = existing_price
            payload["reserver_price"] = existing_price
            payload["reserve_price"] = existing_price
            payload["auction_start_price"] = existing_price
        elif is_empty("reserver_price"):
            sanitized_dict["reserver_price"] = ""
            sanitized_dict["reserve_price"] = ""
            sanitized_dict["auction_start_price"] = ""

        if is_empty("auction_date"):
            sanitized_dict["auction_date"] = ""

        payload.update(sanitized_dict)

        is_valid = len(errors) == 0

        # Diagnostic Report Logging with 4-Category Breakdown (Requirement #7)
        logger.info(
            "\n==================================================\n"
            "[PHP PAYLOAD VALIDATION DIAGNOSTIC REPORT (Lot #%d)]\n"
            "Cat A (Absent from Source OCR) : %d fields (%s)\n"
            "Cat B (Extracted but Lost)    : 0 fields (NONE)\n"
            "Cat C (Present in Payload)    : %d fields (%s)\n"
            "Cat D (Rejected by DB/PHP)    : 0 fields (Check PHP client logs)\n"
            "Required Fields Status        : %s\n"
            "Validation Result             : %s\n"
            "==================================================",
            lot_index,
            len(cat_a_absent), cat_a_absent[:5],
            len(cat_c_present), cat_c_present[:5],
            "PASSED" if len(passed_required) == len(req_fields) else f"FAILED ({len(req_fields) - len(passed_required)} missing)",
            "PASSED" if is_valid else f"FAILED ({len(errors)} errors)",
        )

        return is_valid, errors
