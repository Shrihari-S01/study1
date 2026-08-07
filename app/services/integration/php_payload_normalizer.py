"""
Centralized Schema-Driven PHP Payload Normalizer & Datatype Converter.

Completely schema-driven database constraint enforcement and datatype conversion layer.
Validates and converts every mapped PHP payload field against the central PHP_SCHEMA_SPEC before HTTP POST dispatch.

Features:
- Centralized PHP_SCHEMA_SPEC mapping datatypes (INTEGER, FLOAT, VARCHAR, DATETIME) and max lengths.
- Automatic enum mapping (e.g. 'E-Auction' -> 1, 'Physical' -> 2, 'Pending' -> 'N').
- String formatting cleanup (spaces, duplicate whitespace, line breaks, repeated commas, smart quotes).
- Domain-specific intelligent normalizers (first_bid_acceptance_condition, product_location, institution_seller).
- Word-boundary non-splitting graceful truncation.
- Structured debug logging per field: Field Name, Expected Type, Actual Type, Original Value, Normalized Value, Length, Validation Result.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)

# Centralized Database Schema Specification (PHP_SCHEMA_SPEC)
PHP_SCHEMA_SPEC: Dict[str, Dict[str, Any]] = {
    # 1. Identifiers & Master IDs
    "auction_type": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2, 3],
        "enum_map": {
            "forward auction": 1,
            "forward": 1,
            "e-auction sale": 1,
            "e-auction": 1,
            "eauction": 1,
            "e auction": 1,
            "online": 1,
            "1": 1,
            "reverse auction": 2,
            "reverse": 2,
            "2": 2,
            "tender": 3,
            "tender cum auction": 3,
            "sealed bid": 3,
            "sealed": 3,
            "3": 3,
        },
        "default": 1,
    },
    "p_auction_type": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2, 3],
        "enum_map": {
            "forward auction": 1,
            "forward": 1,
            "e-auction sale": 1,
            "e-auction": 1,
            "eauction": 1,
            "e auction": 1,
            "online": 1,
            "1": 1,
            "reverse auction": 2,
            "reverse": 2,
            "2": 2,
            "tender": 3,
            "tender cum auction": 3,
            "sealed bid": 3,
            "sealed": 3,
            "3": 3,
        },
        "default": 1,
    },
    "wallet": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2],
        "enum_map": {
            "organization": 1,
            "org": 1,
            "1": 1,
            "vendor": 2,
            "2": 2,
        },
        "default": 1,
    },
    "p_wallet": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2],
        "enum_map": {
            "organization": 1,
            "org": 1,
            "1": 1,
            "vendor": 2,
            "2": 2,
        },
        "default": 1,
    },
    "payment_type": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2],
        "enum_map": {
            "online": 1,
            "rtgs": 1,
            "neft": 1,
            "1": 1,
            "offline": 2,
            "dd": 2,
            "demand draft": 2,
            "cheque": 2,
            "2": 2,
        },
        "default": 1,
    },
    "p_payment_type": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2],
        "enum_map": {
            "online": 1,
            "rtgs": 1,
            "neft": 1,
            "1": 1,
            "offline": 2,
            "dd": 2,
            "demand draft": 2,
            "cheque": 2,
            "2": 2,
        },
        "default": 1,
    },
    "vendor_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": True},
    "p_vendor_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": False},
    "section_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": True},
    "p_section_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": False},
    "part_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": True},
    "p_part_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": False},
    "category_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": False},
    "item_id": {"type": "INTEGER", "max_length": 11, "default": 0, "required": False},

    # 2. Location & Parties (VARCHAR)
    "product_location": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},
    "p_product_location": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},
    "borrower_name": {"type": "VARCHAR", "max_length": 255, "required": False, "default": ""},
    "p_borrower_name": {"type": "VARCHAR", "max_length": 255, "required": False, "default": ""},
    "institution_seller": {"type": "VARCHAR", "max_length": 150, "required": False, "default": ""},
    "p_institution_seller": {"type": "VARCHAR", "max_length": 150, "required": False, "default": ""},
    "vendor_name": {"type": "VARCHAR", "max_length": 150, "required": False, "default": ""},
    "auction_number": {"type": "VARCHAR", "max_length": 50, "required": True},
    "p_auction_number": {"type": "VARCHAR", "max_length": 50, "required": False, "default": ""},
    "auction_breif": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},
    "auction_office": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},
    "auction_department": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},
    "first_bid_acceptance_condition": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},
    "p_first_bid_acceptance_condition": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},
    "digital_certificate": {"type": "VARCHAR", "max_length": 100, "required": False, "default": ""},

    # 3. Status & Flag Fields (ENUM)
    "p_dsc": {
        "type": "ENUM",
        "max_length": 1,
        "allowed_values": ["Y", "N"],
        "enum_map": {
            "required": "Y", "yes": "Y", "true": "Y", "1": "Y", "applicable": "Y", "enable": "Y", "enabled": "Y", "y": "Y",
            "not required": "N", "no": "N", "false": "N", "0": "N", "disabled": "N", "none": "N", "n/a": "N", "n": "N"
        },
        "default": "N",
    },
    "dsc": {
        "type": "ENUM",
        "max_length": 1,
        "allowed_values": ["Y", "N"],
        "enum_map": {
            "required": "Y", "yes": "Y", "true": "Y", "1": "Y", "applicable": "Y", "enable": "Y", "enabled": "Y", "y": "Y",
            "not required": "N", "no": "N", "false": "N", "0": "N", "disabled": "N", "none": "N", "n/a": "N", "n": "N"
        },
        "default": "N",
    },
    "auction_live_status": {
        "type": "ENUM",
        "max_length": 1,
        "allowed_values": ["Y", "P", "C", "N"],
        "enum_map": {
            "live": "Y", "active": "Y", "y": "Y", "1": "Y",
            "reschedule": "P", "pending": "P", "p": "P", "0": "P",
            "cancel": "C", "cancelled": "C", "c": "C",
            "not active": "N", "inactive": "N", "n": "N"
        },
        "default": "N",
    },
    "p_auction_live_status": {
        "type": "ENUM",
        "max_length": 1,
        "allowed_values": ["Y", "P", "C", "N"],
        "enum_map": {
            "live": "Y", "active": "Y", "y": "Y", "1": "Y",
            "reschedule": "P", "pending": "P", "p": "P", "0": "P",
            "cancel": "C", "cancelled": "C", "c": "C",
            "not active": "N", "inactive": "N", "n": "N"
        },
        "default": "N",
    },
    "auction_auto_extension": {
        "type": "ENUM",
        "max_length": 1,
        "allowed_values": ["Y", "N"],
        "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N"},
        "default": "N",
    },
    "p_auction_auto_extension": {
        "type": "ENUM",
        "max_length": 1,
        "allowed_values": ["Y", "N"],
        "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N"},
        "default": "N",
    },

    # Gold Carat Flags (ENUM Y or N)
    "sum_of_18_carat": {"type": "ENUM", "max_length": 1, "allowed_values": ["Y", "N"], "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N", "-": "N", "none": "N", "n/a": "N"}, "default": "N"},
    "sum_of_19_carat": {"type": "ENUM", "max_length": 1, "allowed_values": ["Y", "N"], "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N", "-": "N", "none": "N", "n/a": "N"}, "default": "N"},
    "sum_of_20_carat": {"type": "ENUM", "max_length": 1, "allowed_values": ["Y", "N"], "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N", "-": "N", "none": "N", "n/a": "N"}, "default": "N"},
    "sum_of_21_carat": {"type": "ENUM", "max_length": 1, "allowed_values": ["Y", "N"], "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N", "-": "N", "none": "N", "n/a": "N"}, "default": "N"},
    "sum_of_22_carat": {"type": "ENUM", "max_length": 1, "allowed_values": ["Y", "N"], "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N", "-": "N", "none": "N", "n/a": "N"}, "default": "N"},
    "sum_of_23_carat": {"type": "ENUM", "max_length": 1, "allowed_values": ["Y", "N"], "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N", "-": "N", "none": "N", "n/a": "N"}, "default": "N"},
    "sum_of_24_carat": {"type": "ENUM", "max_length": 1, "allowed_values": ["Y", "N"], "enum_map": {"y": "Y", "yes": "Y", "true": "Y", "1": "Y", "n": "N", "no": "N", "false": "N", "0": "N", "-": "N", "none": "N", "n/a": "N"}, "default": "N"},

    "event_type": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2, 3, 4, 14],
        "enum_map": {
            "sarfaesi act": 14,
            "sarfaesi": 14,
            "securitisation": 14,
            "drt": 2,
            "debt recovery tribunal": 2,
            "nclt": 3,
            "insolvency": 3,
            "repo": 4,
            "repossessed": 4,
            "consumer/seller": 1,
            "consumer": 1,
            "seller": 1,
            "14": 14,
            "2": 2,
            "3": 3,
            "4": 4,
            "1": 1,
        },
        "default": 14,
    },
    "p_event_type": {
        "type": "ENUM",
        "max_length": 11,
        "allowed_values": [1, 2, 3, 4, 14],
        "enum_map": {
            "sarfaesi act": 14,
            "sarfaesi": 14,
            "securitisation": 14,
            "drt": 2,
            "debt recovery tribunal": 2,
            "nclt": 3,
            "insolvency": 3,
            "repo": 4,
            "repossessed": 4,
            "consumer/seller": 1,
            "consumer": 1,
            "seller": 1,
            "14": 14,
            "2": 2,
            "3": 3,
            "4": 4,
            "1": 1,
        },
        "default": 14,
    },

    # 4. Numeric & Pricing (DECIMAL)
    "reserver_price": {"type": "DECIMAL", "max_length": 50},
    "p_reserver_price": {"type": "DECIMAL", "max_length": 50},
    "auction_start_price": {"type": "DECIMAL", "max_length": 50},
    "increment_price": {"type": "DECIMAL", "max_length": 50},
    "emd_price": {"type": "DECIMAL", "max_length": 50},

    # 5. Dates & Times (DATE / DATETIME)
    "auction_date": {"type": "DATE", "max_length": 20},
    "p_auction_date": {"type": "DATE", "max_length": 20},
    "emd_submission_date": {"type": "DATE", "max_length": 20},
    "p_emd_submission_date": {"type": "DATE", "max_length": 20},
    "inspection_date_time": {"type": "DATETIME", "max_length": 30},

    # 6. EMD Bank & Account Specific Fields
    "emd_account_no": {"type": "ACCOUNT_NO", "max_length": 50},
    "p_emd_account_no": {"type": "ACCOUNT_NO", "max_length": 50},
    "emd_ifsc": {"type": "IFSC", "max_length": 20},
    "p_emd_ifsc": {"type": "IFSC", "max_length": 20},
    "emd_bank_name": {"type": "BANK_NAME", "max_length": 150},
    "p_emd_bank_name": {"type": "BANK_NAME", "max_length": 150},

    # 7. Phone Number Fields
    "authorized_officer_no": {"type": "PHONE", "max_length": 50},
    "authorized_officer_phone": {"type": "PHONE", "max_length": 50},
    "p_authorized_officer_no": {"type": "PHONE", "max_length": 50},
    "p_authorized_office_phone": {"type": "PHONE", "max_length": 50},
    "branch_phone": {"type": "PHONE", "max_length": 50},
    "contact_phone": {"type": "PHONE", "max_length": 50},
    "mobile_number": {"type": "PHONE", "max_length": 50},
    "customer_phone": {"type": "PHONE", "max_length": 50},

    # 8. Short Remarks & Descriptions (VARCHAR & TEXT)
    "auction_details": {"type": "TEXT", "max_length": 5000},
    "remarks": {"type": "REMARKS", "max_length": 255},
    "p_remarks": {"type": "REMARKS", "max_length": 255},
}


class CentralizedPHPPayloadNormalizer:
    """
    Centralized schema-driven payload normalizer and datatype converter.
    """

    @staticmethod
    def extract_account_number(raw_val: Any) -> str:
        """
        Extract ONLY the actual account number from raw value:
        - Removes labels ('A/C No', 'Account No', 'Account Number', 'Acc No', 'A/c', 'EMD Account', etc.).
        - Removes surrounding text (bank names, IFSC, RTGS/NEFT instructions, paragraph noise).
        - Isolates pure numeric or valid alphanumeric account tokens (typically 8 to 25 digits/chars).
        - Returns empty string if no valid account number exists (never returns paragraph text or IFSC/Bank).
        - Logs raw extracted value, normalized account number, and character length.
        """
        if not raw_val:
            return ""

        raw_str = str(raw_val).strip()
        if not raw_str or raw_str.lower() in {"none", "null", "undefined", "n/a", "nil"}:
            return ""

        # Step 1: Strip common labels
        label_pattern = r"(?i)\b(emd\s*a/?c\s*no|emd\s*account|a/?c\s*no|account\s*no|account\s*number|acc\s*no|a/?c|account|ac)\b\.?\s*:?"
        clean_s = re.sub(label_pattern, " ", raw_str)

        # Step 2: Remove IFSC, RTGS/NEFT, and Bank words if present in paragraph
        clean_s = re.sub(r"(?i)\b[A-Z]{4}0[A-Z0-9]{6}\b", " ", clean_s)  # Remove IFSC
        clean_s = re.sub(r"(?i)\b(rtgs|neft|mode of payment|payment|bank|ifsc|branch|favouring|in favour of)\b", " ", clean_s)

        normalized_acc = ""

        # Step 3: Find digit sequences or valid alphanumeric account tokens (8 to 25 digits/chars)
        tokens = re.findall(r"\b[A-Z0-9]{8,25}\b", clean_s)

        valid_accs = []
        for t in tokens:
            digits_count = sum(c.isdigit() for c in t)
            # Account numbers must consist predominantly of digits (at least 5 digits) and not be pure words
            if digits_count >= 5 and not t.isalpha():
                valid_accs.append(t)

        if valid_accs:
            # Prefer pure digit strings first if available
            pure_digits = [acc for acc in valid_accs if acc.isdigit()]
            normalized_acc = pure_digits[0] if pure_digits else valid_accs[0]
        else:
            # Fallback: Find longest pure digit sequence between 8 and 25 digits
            digit_matches = re.findall(r"\b\d{8,25}\b", raw_str)
            if digit_matches:
                normalized_acc = digit_matches[0]

        logger.info(
            "\n==================================================\n"
            "[EMD ACCOUNT NUMBER EXTRACTION AUDIT]\n"
            "RAW EXTRACTED VALUE : %r (Len: %d)\n"
            "NORMALIZED ACCOUNT  : %r (Len: %d)\n"
            "==================================================",
            raw_str,
            len(raw_str),
            normalized_acc,
            len(normalized_acc),
        )

        return normalized_acc

    @staticmethod
    def extract_ifsc_code(raw_val: Any) -> str:
        """
        Extract ONLY standard 11-character Indian IFSC code (4 alpha + 0 + 6 alphanumeric).
        """
        if not raw_val:
            return ""
        s = str(raw_val).strip().upper()
        match = re.search(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", s)
        return match.group(0) if match else ""

    @staticmethod
    def extract_bank_name(raw_val: Any) -> str:
        """
        Extract concise bank name (e.g. 'Bank of Baroda', 'State Bank of India', 'Canara Bank').
        """
        if not raw_val:
            return ""
        s = str(raw_val).strip()
        # Remove account numbers, IFSC codes, and paragraph instructions
        s = re.sub(r"(?i)\b[A-Z]{4}0[A-Z0-9]{6}\b", "", s)
        s = re.sub(r"(?i)\b(a/?c\s*no|account\s*no|account\s*number|rtgs|neft)\b.*", "", s)
        
        # Check known major bank names
        for bank in ["Bank of Baroda", "State Bank of India", "Punjab National Bank", "Canara Bank", "Union Bank of India", "Bank of India", "Indian Bank", "Central Bank of India", "ICICI Bank", "HDFC Bank", "Axis Bank", "Kotak Mahindra Bank", "IDBI Bank", "Federal Bank", "Indian Overseas Bank", "UCO Bank", "Punjab & Sind Bank"]:
            if bank.lower() in s.lower():
                return bank

        # Fallback clean string max 150 chars
        clean_bank = re.sub(r"(?i)\s*(regional office|zonal office|sarb|branch|stressed assets recovery branch).*", "", s).strip()
        return clean_bank[:150]

    @staticmethod
    def extract_concise_remark(raw_val: Any, max_length: int = 255) -> str:
        """
        Semantically normalizes and compresses long remarks paragraphs into concise business remarks:
        - Extracts primary semantic context (e.g., '30 Days Statutory Sale Notice', 'SARFAESI Sale Notice', 'Inspection by Appointment').
        - Eliminates verbose legal boilerplate, disclaimers, repeated OCR text, and full paragraph descriptions.
        """
        if not raw_val:
            return ""

        s = str(raw_val).strip()
        if not s or s.lower() in {"none", "null", "undefined", "n/a", "nil"}:
            return ""

        # Step 1: Semantic pattern matching for known core auction remark intents
        patterns = [
            (r"(?i)\b(30\s*days?\s*(statutory)?\s*sale\s*notice)\b", "30 Days Statutory Sale Notice"),
            (r"(?i)\b(15\s*days?\s*(statutory)?\s*sale\s*notice)\b", "15 Days Statutory Sale Notice"),
            (r"(?i)\b(statutory\s*sale\s*notice)\b", "Statutory Sale Notice"),
            (r"(?i)\b(sarfaesi\s*sale\s*notice|sarfaesi\s*notice|sarfaesi\s*act|sarfaesi)\b", "SARFAESI Sale Notice"),
            (r"(?i)\b(drt\s*sale\s*notice)\b", "DRT Sale Notice"),
            (r"(?i)\b(nclt\s*sale\s*notice)\b", "NCLT Sale Notice"),
            (r"(?i)\b(inspection.*appointment|appointment.*inspection|inspection\s*date|date\s*of\s*inspection)\b", "Inspection by Appointment"),
            (r"(?i)\b(emd\s*(via|by)?\s*rtgs/?neft|rtgs/?neft\s*payment|rtgs/?neft)\b", "EMD via RTGS/NEFT"),
            (r"(?i)\b(symbolic\s*possession)\b", "Symbolic Possession"),
            (r"(?i)\b(physical\s*possession)\b", "Physical Possession"),
            (r"(?i)\b(constructive\s*possession)\b", "Constructive Possession"),
        ]

        found_remarks = []
        for pattern, label in patterns:
            if re.search(pattern, s) and label not in found_remarks:
                found_remarks.append(label)

        if found_remarks:
            res = " | ".join(found_remarks)
            return res[:max_length]

        # Step 2: Remove legal disclaimers, boilerplate, and OCR noise
        clean = s.replace("\r\n", " ").replace("\r", " ").replace("\t", " ").replace("\n", " ").replace("\x00", "")
        clean = re.sub(r"(?i)\b(it may be treated as|this is a|notice is hereby given that|under the securitisation and reconstruction of financial assets and enforcement of security interest act|sarfaesi act 2002|read with proviso to rule 8\s*\(6\))\b", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()

        # Step 3: Extract the first sentence if concise or summarize
        sentences = [st.strip() for st in re.split(r"[.\n;]+", clean) if len(st.strip()) > 5]
        if sentences:
            first_sent = sentences[0]
            if len(first_sent) <= max_length:
                return first_sent

        # Step 4: Gracefully truncate at word boundary
        if len(clean) > max_length:
            space_idx = clean[:max_length].rfind(" ")
            clean = clean[:space_idx].strip() if space_idx > 0 else clean[:max_length].strip()

        return clean.rstrip(",.-;/ ")

    @staticmethod
    def parse_and_extract_phone_numbers(raw_val: Any) -> Tuple[List[str], str]:
        """
        Parse raw phone string, remove labels (Mobile/Phone/Tel/Contact),
        split on delimiters (/ , ; & | \n), extract numbers, deduplicate, and select primary phone number.
        """
        if not raw_val:
            return [], ""

        s = str(raw_val).strip()
        label_pattern = r"(?i)\b(mobile|mob|phone|tel|contact|ph|no|office|ext|call|res|fax)\b\.?\s*:?"
        clean_s = re.sub(label_pattern, "", s)

        delimiters = r"[\/,;&|\n]+"
        raw_parts = [p.strip() for p in re.split(delimiters, clean_s) if p.strip()]

        parsed_numbers: List[str] = []
        for part in raw_parts:
            digits = re.sub(r"\D", "", part)
            if len(digits) == 12 and digits.startswith("91"):
                digits = digits[2:]

            if 7 <= len(digits) <= 15 and digits not in parsed_numbers:
                parsed_numbers.append(digits)

        primary = parsed_numbers[0] if parsed_numbers else re.sub(r"\D", "", s)[:15]
        return parsed_numbers, primary

    @staticmethod
    def clean_basic_formatting(val: str) -> str:
        """
        Step 2: Basic string formatting cleanup & SQL-breaking character removal.
        """
        from app.services.integration.payload_sanitizer import sanitize_varchar_field
        return sanitize_varchar_field(val)

    @staticmethod
    def apply_intelligent_field_normalization(field_name: str, val: str, limit: int) -> str:
        """
        Step 3: Domain-specific intelligent normalization.
        """
        if field_name == "p_dsc":
            v = str(val).strip().lower()
            if any(kw in v for kw in ["yes", "y", "true", "1", "applicable", "required", "enable", "enabled"]):
                return "Y"
            return "N"

        if field_name in {"first_bid_acceptance_condition", "p_first_bid_acceptance_condition"}:
            from app.services.integration.normalizer import DataNormalizer
            flag = DataNormalizer.map_first_bid_acceptance_condition(val)
            logger.info(
                "\n==================================================\n"
                "[FIRST BID ACCEPTANCE CONDITION FLAG MAPPING]\n"
                "Field           : %s\n"
                "Original Text   : %r\n"
                "Mapped Flag     : \"%s\"\n"
                "Length          : %d (Limit: %d)\n"
                "Validation      : PASS\n"
                "==================================================",
                field_name,
                val,
                flag,
                len(flag),
                limit,
            )
            return flag

        if field_name in {"borrower_name", "p_borrower_name"}:
            from app.services.integration.normalizer import DataNormalizer
            clean_b, _ = DataNormalizer.separate_borrower_name_and_address(val)
            if clean_b:
                return clean_b

        if field_name in {"product_location", "p_product_location"}:
            from app.services.integration.normalizer import DataNormalizer
            derived = DataNormalizer.derive_product_location({"property_address": val})
            if derived and len(derived) <= limit:
                return derived

        if field_name in {"institution_seller", "p_institution_seller", "vendor_name"}:
            for bank_name in ["Bank of Baroda", "State Bank of India", "Punjab National Bank", "Canara Bank", "Union Bank of India", "Bank of India", "Indian Bank", "Central Bank of India"]:
                if bank_name.lower() in val.lower():
                    return bank_name
            s = re.sub(r"(?i)\s*(regional office|zonal office|sarb|branch|stressed assets recovery branch).*", "", val).strip()
            if s:
                return s

        if field_name in {"auction_live_status", "p_auction_live_status"}:
            from app.services.integration.normalizer import DataNormalizer
            return DataNormalizer.normalize_live_status_code(val)

        if field_name in {"event_type", "p_event_type"}:
            from app.services.integration.normalizer import DataNormalizer
            detected_event = DataNormalizer.detect_legal_event_type({"event_type": val})
            spec = PHP_SCHEMA_SPEC.get(field_name, {})
            enum_map = spec.get("enum_map", {})
            event_id = enum_map.get(detected_event.lower(), 14)
            logger.info(
                "\n==================================================\n"
                "[EVENT TYPE LEGAL CONTEXT RESOLUTION]\n"
                "Detected Legal Context: %s\n"
                "Matched Master        : event_id = %d\n"
                "auction_type          : E-Auction (ID: 1)\n"
                "Validation            : PASS\n"
                "==================================================",
                detected_event,
                event_id,
            )
            return str(event_id)

        return val

    @staticmethod
    def generic_intelligent_shorten(text: str, max_length: int) -> Tuple[str, str]:
        """
        Steps 3 & 4: Generic intelligent text shortener:
        1. Summarizes common verbose legalese/condition phrases while preserving semantic meaning.
        2. Safely truncates at word boundaries if summarization still exceeds limit (never splitting words).
        Returns (shortened_text, transformation_type).
        """
        if not text or len(text) <= max_length:
            return text, "Cleaned"

        # Phrase replacement dictionary for generic legal/auction boilerplate
        summarization_rules = [
            (r"(?i)\bthe aforesaid properties shall not be sold below the reserve price mentioned above\b", "Property will not be sold below reserve price"),
            (r"(?i)\bthe property shall not be sold below the reserve price\b", "Property not sold below reserve price"),
            (r"(?i)\bsubject to confirmation by the authorized officer\b", "Subject to officer confirmation"),
            (r"(?i)\bsubject to confirmation of the secured creditor\b", "Subject to creditor confirmation"),
            (r"(?i)\bfirst bid acceptance condition\b", "First bid condition"),
            (r"(?i)\bas is where is basis\b", "As Is Where Is"),
            (r"(?i)\bas is what is basis\b", "As Is What Is"),
            (r"(?i)\bwhatever there is basis\b", "Whatever There Is"),
            (r"(?i)\bwithout any recourse\b", "Without Recourse"),
        ]

        summarized = text
        for pattern, replacement in summarization_rules:
            summarized = re.sub(pattern, replacement, summarized)

        summarized = re.sub(r"\s+", " ", summarized).strip()
        if len(summarized) <= max_length:
            return summarized, "Summarized"

        # Word boundary truncation
        truncated = summarized[:max_length]
        if " " in truncated and len(summarized) > max_length:
            truncated = truncated.rsplit(" ", 1)[0]

        truncated = truncated.strip().rstrip(",.-;/")
        return truncated, "Summarized & Truncated at Word Boundary"

    @staticmethod
    def truncate_gracefully_at_word_boundary(val: str, limit: int) -> str:
        """
        Step 4: Truncate gracefully at nearest word/space boundary without splitting words or UTF characters.
        """
        if len(val) <= limit:
            return val

        space_idx = val[:limit].rfind(" ")
        if space_idx > 0:
            truncated = val[:space_idx].strip()
        else:
            truncated = val[:limit].strip()

        return truncated.rstrip(",.-;/")

    @classmethod
    def convert_value_by_spec(cls, field_name: str, raw_val: Any, spec: Dict[str, Any]) -> Tuple[Any, str]:
        """
        Convert, normalize, and validate field value based on schema specification.
        Supports: ENUM, VARCHAR, TEXT, INTEGER, DATE, DATETIME, DECIMAL.
        """
        target_type = str(spec.get("type", "VARCHAR")).upper()
        max_len = spec.get("max_length", 255)
        enum_map = spec.get("enum_map")
        allowed_values = spec.get("allowed_values")
        default_val = spec.get("default")

        if raw_val is None or str(raw_val).strip() == "":
            if default_val is not None:
                return default_val, "PASS"
            return "", "PASS"

        val_str = str(raw_val).strip()

        # 1. ENUM Datatype Engine
        if target_type == "ENUM":
            norm_lower = val_str.lower()
            res_val = None

            if enum_map and isinstance(enum_map, dict) and norm_lower in enum_map:
                res_val = enum_map[norm_lower]
            elif allowed_values:
                for av in allowed_values:
                    if str(av).lower() == norm_lower:
                        res_val = av
                        break

            if res_val is None:
                if default_val is not None:
                    res_val = default_val
                else:
                    res_val = val_str

            is_allowed = True
            if allowed_values:
                is_allowed = (res_val in allowed_values) or any(str(av) == str(res_val) for av in allowed_values)

            if not is_allowed:
                return str(res_val)[:max_len], f"REJECTED: Value '{val_str}' not in allowed ENUM values {allowed_values}"

            if len(str(res_val)) > max_len:
                return str(res_val)[:max_len], f"REJECTED: ENUM value '{res_val}' exceeds max length {max_len}"

            return res_val, "ENUM_MAPPED" if str(res_val) != val_str else "PASS"

        # 2. INTEGER Datatype Engine
        if target_type == "INTEGER":
            norm_str = cls.apply_intelligent_field_normalization(field_name, val_str, max_len)
            norm_lower = norm_str.lower()

            if enum_map and isinstance(enum_map, dict) and norm_lower in enum_map:
                res_id = int(enum_map[norm_lower])
                return res_id, "ENUM_MAPPED"

            clean_num = re.sub(r"[^\d-]", "", norm_str)
            if clean_num:
                try:
                    res_id = int(clean_num)
                    if len(str(res_id)) > max_len:
                        return res_id, f"REJECTED: Integer length exceeds max length {max_len}"
                    return res_id, "PASS"
                except ValueError:
                    pass

            if default_val is not None:
                return int(default_val), "PASS"
            return 0, "PASS"

        # 3. DECIMAL / FLOAT Datatype Engine
        if target_type in {"FLOAT", "DECIMAL"}:
            clean_num_str = re.sub(r"(?i)\b(rs|inr|rupees)\b\.?\s*", "", val_str)
            clean_flt = re.sub(r"[^\d.]", "", clean_num_str).lstrip(".")
            if clean_flt:
                try:
                    flt = float(clean_flt)
                    res_num = int(flt) if flt.is_integer() else f"{flt:.2f}"
                    if len(str(res_num)) > max_len:
                        return str(res_num)[:max_len], f"REJECTED: Numeric value exceeds max length {max_len}"
                    return res_num, "PASS"
                except ValueError:
                    pass
            return "0", "PASS"

        # 4. DATE / DATETIME Datatype Engine
        if target_type in {"DATE", "DATETIME"}:
            cleaned_date = cls.clean_basic_formatting(val_str)
            if len(cleaned_date) > max_len:
                return cleaned_date[:max_len], "TRUNCATED"
            return cleaned_date, "PASS"

        # 5. Specific Domain Handlers: ACCOUNT_NO, IFSC, BANK_NAME, REMARKS, PHONE
        if target_type == "ACCOUNT_NO" or "account_no" in field_name.lower():
            clean_acc = cls.extract_account_number(val_str)
            return clean_acc[:max_len], "PASS"

        if target_type == "IFSC" or "ifsc" in field_name.lower():
            clean_ifsc = cls.extract_ifsc_code(val_str)
            return clean_ifsc[:max_len], "PASS"

        if target_type == "BANK_NAME" or "bank_name" in field_name.lower():
            clean_bank = cls.extract_bank_name(val_str)
            return clean_bank[:max_len], "PASS"

        if target_type == "REMARKS" or "remarks" in field_name.lower() or "remark" in field_name.lower():
            clean_remark = cls.extract_concise_remark(val_str, max_length=max_len)
            return clean_remark[:max_len], "PASS"

        is_phone_field = (
            target_type == "PHONE" or
            any(kw in field_name.lower() for kw in ["phone", "mobile", "contact_no", "officer_no", "tel_no"])
        )

        if is_phone_field:
            parsed_numbers, primary_phone = cls.parse_and_extract_phone_numbers(val_str)
            return primary_phone[:max_len], "PASS"

        # 6. VARCHAR & TEXT Datatype Engine
        cleaned_str = cls.clean_basic_formatting(val_str)
        norm_str = cls.apply_intelligent_field_normalization(field_name, cleaned_str, max_len)
        norm_lower = norm_str.lower()

        if enum_map and isinstance(enum_map, dict) and norm_lower in enum_map:
            final_str = str(enum_map[norm_lower])
            trans_type = "ENUM_MAPPED"
        else:
            final_str, trans_type = cls.generic_intelligent_shorten(norm_str, max_len)

        if len(final_str) > max_len:
            final_str = cls.truncate_gracefully_at_word_boundary(final_str, max_len)
            trans_type = "TRUNCATED"

        return final_str, trans_type

    @classmethod
    def normalize_payload(cls, payload: Dict[str, Any], processing_id: str = "N/A") -> Dict[str, Any]:
        """
        Centralized payload normalizer for all PHP API requests.
        Delegates to PHPSanitizer to create a new, 100% sanitized & schema-validated payload object.
        """
        from app.services.integration.payload_sanitizer import PHPSanitizer
        return PHPSanitizer.sanitize_payload(payload, processing_id=processing_id)
