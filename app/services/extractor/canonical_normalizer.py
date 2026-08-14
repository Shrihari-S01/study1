"""
Canonical Field Alias Normalization Layer.

Single, unified normalization layer for all auction field aliases.
Resolves field key variations BEFORE validation and mapping, ensuring
non-empty extracted values are preserved and never overwritten by null, "", or "0".
Strictly separates phone numbers, IFSC codes, EMD account numbers, and loan account numbers.
Enforces distinct semantic mapping: reserve_price and auction_start_price do NOT overwrite each other.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List
from app.core.logger import get_logger

logger = get_logger(__name__)

class CanonicalAliasNormalizer:
    """
    Unified canonical alias normalizer.
    Enforces non-empty value preservation across alias key sets.
    """

    @staticmethod
    def is_phone_number(val: str) -> bool:
        """
        Check if a string represents a phone number or officer contact number.
        e.g. 05222307898, 9876543210, +919876543210, 0522-2307898
        """
        if not val:
            return False
        clean = re.sub(r"[\s\-\(\)\+]", "", val)
        if clean.startswith("91") and len(clean) == 12:
            clean = clean[2:]
        if clean.startswith("0") and 10 <= len(clean) <= 12 and clean.isdigit():
            return True
        if len(clean) == 10 and clean.isdigit() and clean[0] in "67895":
            return True
        if 7 <= len(clean) <= 12 and clean.isdigit():
            return True
        return False

    @classmethod
    def normalize_loan_account_number(cls, val: Any, officer_phone: str = "", contact_phone: str = "", emd_account: str = "", ifsc: str = "") -> str:
        """
        Validate loan_account_number semantics.
        Never use phone numbers, officer numbers, IFSCs, or EMD account numbers as loan_account_number.
        If loan_account_number cannot be confidently identified, returns "".
        """
        if not val:
            return ""
        s = str(val).strip()
        if not s or s.lower() in {"null", "none", "n/a", "undefined", "0", "nil", ""}:
            return ""

        # Reject if value matches any known phone number in document or is generic phone format
        if cls.is_phone_number(s):
            logger.info("Semantic Guard: Clearing phone number '%s' incorrectly passed as loan_account_number", s)
            return ""

        # Reject if value matches officer phone or contact phone
        if officer_phone and re.sub(r"\D", "", s) and re.sub(r"\D", "", s) in re.sub(r"\D", "", officer_phone):
            logger.info("Semantic Guard: Clearing officer phone '%s' passed as loan_account_number", s)
            return ""

        if contact_phone and re.sub(r"\D", "", s) and re.sub(r"\D", "", s) in re.sub(r"\D", "", contact_phone):
            logger.info("Semantic Guard: Clearing contact phone '%s' passed as loan_account_number", s)
            return ""

        # Reject if value is IFSC code
        if re.search(r"^[A-Z]{4}0[A-Z0-9]{6}$", s.replace(" ", "").upper()):
            return ""

        # Reject if value matches EMD account number exactly
        if emd_account and s == emd_account:
            logger.info("Semantic Guard: Clearing EMD account number '%s' passed as loan_account_number", s)
            return ""

        # Remove labels if present
        clean_lan = re.sub(r"(?i)^(loan\s*(account|a/c|no|number)?|lan|account\s*no\.?)\s*[:.-]?\s*", "", s).strip()
        if not clean_lan or cls.is_phone_number(clean_lan):
            return ""

        return clean_lan

    @classmethod
    def normalize_record_aliases(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Populates all alias representations for every non-empty field key.
        Prevents later stages from overwriting canonical non-empty values with null or empty string.
        """
        if not isinstance(record, dict):
            return {}

        norm = dict(record)

        def first_non_empty(*keys) -> str:
            for k in keys:
                val = norm.get(k)
                if val is not None:
                    s = str(val).strip()
                    if s and s.lower() not in {"null", "none", "n/a", "undefined"}:
                        return s
            return ""

        def first_non_empty_monetary(*keys) -> Any:
            for k in keys:
                val = norm.get(k)
                if val is not None:
                    s = str(val).strip()
                    if s and s not in {"0", "0.0", "0.00", "null", "none", "n/a", "undefined"}:
                        return val
            return ""

        # 0. Auction Number Aliases
        auc_num = first_non_empty("auction_number", "p_auction_number", "auction_no", "notice_auction_id", "auction_id")
        if auc_num:
            norm["auction_number"] = auc_num
            norm["p_auction_number"] = auc_num
            norm["auction_no"] = auc_num

        # 1. Reserve Price Aliases (Do NOT map into auction_start_price)
        rp = first_non_empty_monetary(
            "reserve_price", "reserver_price", "reserve_amount", "reserve_rate", "upset_price", "base_price"
        )
        if rp:
            norm["reserve_price"] = rp
            norm["reserver_price"] = rp
            norm["p_reserver_price"] = rp

        # 2. Auction Start Price Aliases (Do NOT map into reserve_price)
        asp = first_non_empty_monetary(
            "auction_start_price", "starting_price", "start_price", "starting_bid", "opening_bid", "start_floor_price"
        )
        if asp:
            norm["auction_start_price"] = asp
            norm["starting_price"] = asp

        # 3. EMD Amount / Price Aliases
        emd = first_non_empty_monetary(
            "emd_amount", "emd_price", "pre_bid_emd", "emd_value", "deposit_amount"
        )
        if emd:
            norm["emd_amount"] = emd
            norm["emd_price"] = emd
            norm["pre_bid_emd"] = emd

        # 4. Increment Price Aliases
        inc = first_non_empty_monetary(
            "increment_price", "bid_increment", "bid_increase_amount", "bid_increase",
            "increase_amount", "min_bid_increment", "bid_increment_amount"
        )
        if inc:
            norm["increment_price"] = inc
            norm["bid_increment"] = inc

        # 5. Borrower Name Aliases
        bor = first_non_empty(
            "borrower_name", "borrower", "borrower_details", "borrower_s",
            "applicant_name", "mortgagor_name", "guarantor_name", "co_borrower"
        )
        if bor:
            norm["borrower_name"] = bor
            norm["borrower"] = bor
            norm["p_borrower_name"] = bor

        # 6. Loan Account Number Validation & Cleanup
        raw_lan = first_non_empty("loan_account_number", "loan_number", "loan_no", "loan_account_no", "lan_no", "loan_account")
        officer_phone = first_non_empty("authorized_officer_number", "authorized_officer_no", "authorized_officer_phone", "contact_number")
        contact_phone = first_non_empty("contact_phone", "branch_phone", "mobile_number")
        emd_acc = first_non_empty("emd_account_no", "emd_account_number")
        ifsc_val = first_non_empty("emd_ifsc", "ifsc")

        clean_lan = cls.normalize_loan_account_number(
            raw_lan, officer_phone=officer_phone, contact_phone=contact_phone, emd_account=emd_acc, ifsc=ifsc_val
        )
        norm["loan_account_number"] = clean_lan
        norm["loan_number"] = clean_lan
        norm["loan_no"] = clean_lan

        # 7. Property Description & Address
        desc = first_non_empty("auction_description", "auction_details", "description", "property_description", "auction_breif")
        addr = first_non_empty("property_address", "assets_location", "product_location", "location", "address")

        if not desc and addr:
            desc = addr
        elif not addr and desc:
            addr = desc

        if desc:
            norm["auction_description"] = desc
            norm["auction_details"] = desc
            norm["description"] = desc
            norm["auction_breif"] = desc[:100]
        if addr:
            norm["property_address"] = addr
            norm["assets_location"] = addr
            norm["product_location"] = addr
            norm["p_product_location"] = addr

        # 8. EMD Bank, Account, IFSC
        if emd_acc:
            norm["emd_account_no"] = emd_acc
            norm["emd_account_number"] = emd_acc
            norm["p_emd_account_no"] = emd_acc
        if ifsc_val:
            norm["emd_ifsc"] = ifsc_val
            norm["ifsc"] = ifsc_val
            norm["p_emd_ifsc"] = ifsc_val

        return norm
