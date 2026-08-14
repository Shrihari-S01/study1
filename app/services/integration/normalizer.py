"""
Data Normalization Layer.

Stage 4: Cleans and standardizes raw field values in the CommonAISchema dictionary
(stripping currency symbols, formatting dates to ISO, cleaning text, mapping boolean flags).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)

class DataNormalizer:
    """
    Normalizes text, dates, monetary strings, and enums prior to key payload mapping.
    """

    ADDRESS_INDICATOR_REGEX = re.compile(
        r"""(?ix)
        \b(
            having\s+(registered\s+)?(address|office)(\s+at)? |
            registered\s+office(\s+at)? |
            regd\.?\s*off(ice)?(\s+at)? |
            address\s+at |
            address\s*: |
            \br/?o\b |
            residing\s+at |
            situated\s+at |
            located\s+at |
            at\s+village |
            \bvillage\s*[-:]? |
            \bvpo\s*[-:]? |
            \bdoor\s*no\b\.? |
            \bplot\s*no\b\.? |
            \bsurvey\s*no\b\.? |
            \bh\.?no\b\.? |
            \bflat\s*no\b\.? |
            \bstreet\b |
            \broad\b |
            \bdistrict\b |
            \bstate\b |
            \bpin\s*code\b |
            \bpin\s*:?\s*\d{5,6}
        )\b
        """
    )

    @classmethod
    def separate_borrower_name_and_address(cls, raw_text: Any) -> Tuple[str, str]:
        """
        Separates legal borrower/entity name from address text using semantic indicators.
        Returns Tuple[clean_borrower_name, extracted_address_text].
        
        1. Detects address indicators: 'having registered address', 'registered office', 'address at',
           'r/o', 'residing at', 'situated at', 'village', 'plot no', 'door no', 'survey no', 'PIN', etc.
        2. Cuts text at the first address indicator boundary.
        3. Normalizes proprietor notation: e.g. ', prop. Mrs. Madhu Gupta' -> ' (Prop. Mrs. Madhu Gupta)'.
        4. Returns clean entity name and extracted address segment.
        """
        if not raw_text:
            return "", ""

        s = str(raw_text).strip()
        if not s or s.lower() in {"null", "none", "undefined", "n/a"}:
            return "", ""

        match = cls.ADDRESS_INDICATOR_REGEX.search(s)

        clean_borrower = s
        extracted_address = ""

        if match:
            borrower_raw = s[:match.start()].strip().rstrip(",.-;:")
            address_raw = s[match.start():].strip()

            clean_addr = re.sub(
                r"(?ix)^\s*(having\s+(registered\s+)?(address|office)(\s+at)?|registered\s+office(\s+at)?|regd\.?\s*off(ice)?(\s+at)?|address\s+at|address\s*:|\br/?o\b|residing\s+at|situated\s+at|located\s+at|at\s+village)\s*[-:]?\s*",
                "",
                address_raw
            ).strip().lstrip(",.-;:")

            clean_borrower = borrower_raw
            extracted_address = clean_addr

        # Clean & normalize proprietor patterns in borrower name if present
        prop_pattern = r"(?i),\s*(prop\.?|proprietor|proprietress)\s*:?\s*([A-Za-z0-9\.\s]+)$"
        prop_match = re.search(prop_pattern, clean_borrower)

        if prop_match:
            entity = clean_borrower[:prop_match.start()].strip().rstrip(",.-;:")
            prop_name = prop_match.group(2).strip()
            if entity and prop_name:
                clean_borrower = f"{entity} (Prop. {prop_name})"
            elif prop_name:
                clean_borrower = f"Prop. {prop_name}"

        clean_borrower = cls.restore_legal_abbreviations(clean_borrower)

        if extracted_address:
            logger.info(
                "\n==================================================\n"
                "[BORROWER & ADDRESS SEMANTIC SEPARATION LOG]\n"
                "Raw Input Text   : %r\n"
                "Clean Borrower   : %r\n"
                "Extracted Address: %r\n"
                "==================================================",
                s,
                clean_borrower,
                extracted_address,
            )

        return clean_borrower, extracted_address

    @staticmethod
    def restore_legal_abbreviations(text: str) -> str:
        if not text:
            return text
        s = str(text)
        s = re.sub(r"(?i)\bM\s*[\,\\\.\s]\s*s\b", "M/s", s)
        s = re.sub(r"(?i)\bM\s*[\,\\\.]\s*S\b", "M/s", s)
        s = re.sub(r"(?i)\bMrs(?:\.|\b)", "Mrs.", s)
        s = re.sub(r"(?i)\bMr(?:\.|\b)", "Mr.", s)
        s = re.sub(r"(?i)\bDr(?:\.|\b)", "Dr.", s)
        s = re.sub(r"(?i)\bPvt(?:\.|\b)", "Pvt.", s)
        s = re.sub(r"(?i)\bLtd(?:\.|\b)", "Ltd.", s)
        s = re.sub(r"(?i)\bCo(?:\.|\b)", "Co.", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    @staticmethod
    def map_first_bid_acceptance_condition(text: Any) -> str:
        """
        Map first bid acceptance condition to a YES/NO flag for PHP Payload.
        Full extracted sentence is preserved in AI extraction JSON for UI display.
        Logic:
          - If text contains any auction acceptance clause ("As is where is", "As is what is",
            "Whatever there is", "Without recourse", "Without warranty", etc.), return "YES".
          - Otherwise, return "NO".
        """
        if not text:
            return "NO"

        s = str(text).strip()
        if not s or s.lower() in {"none", "null", "undefined", "n/a", "no", "false", "0"}:
            return "NO"

        s_lower = s.lower()
        if any(kw in s_lower for kw in [
            "as is", "where is", "what is", "whatever", "recourse", "warranty",
            "reserve price", "sold", "acceptance", "condition", "yes", "true", "1"
        ]) or len(s) > 2:
            return "YES"

        return "NO"

    LIVE_STATUS_MAP = {
        "pending": "N",
        "p": "N",
        "0": "N",
        "n": "N",
        "upcoming": "N",
        "u": "N",

        "live": "Y",
        "active": "Y",
        "y": "Y",
        "1": "Y",

        "closed": "C",
        "c": "C",

        "completed": "D",
        "done": "D",
        "d": "D",
    }

    @staticmethod
    def normalize_live_status_code(raw_status: Any) -> str:
        """
        Map human text 'Pending' / 'Live' / 'Closed' / 'Completed' to 1-character database code:
        - 'Pending' -> 'N'
        - 'Live' -> 'Y'
        - 'Closed' -> 'C'
        - 'Completed' -> 'D'
        """
        if raw_status is None:
            return "N"
        val_str = str(raw_status).strip()
        mapped_code = DataNormalizer.LIVE_STATUS_MAP.get(val_str.lower(), "N")
        logger.info("Normalizing auction_live_status: before='%s' -> after='%s'", val_str, mapped_code)
        return mapped_code

    NOISE_PATTERNS = [
        # Door, plot, survey, house, flat, khasra, unit numbers, codes
        r"(?i)\b(plot|survey|door|flat|house|h\.?no|khasra|khata|unit|bxxx|b-?\d+)\b",
        # Landmarks starting with Opp, Near, Behind, Beside, Adj, Opposite, Adjacent
        r"(?i)^\s*(opp|near|behind|beside|adj|opposite|adjacent)\b",
        # Streets, roads, lanes
        r"(?i)\b(road|rd|g\.?t\.?\s*road|street|st|lane|marg|chowk|bypass)\b",
        # State names (at end of segment)
        r"(?i)\b(punjab|tamil nadu|haryana|delhi|maharashtra|karnataka|gujarat|rajasthan|uttar pradesh|west bengal|kerala|andhra pradesh|telangana)\s*\d*$",
        # PIN codes or pure numeric patterns
        r"\b\d{5,6}\b",
        r"(?i)\bpin\s*:?\s*\d+",
    ]

    @staticmethod
    def derive_product_location(data: Dict[str, Any]) -> str:
        """
        Derive a concise, searchable product_location (max 100 characters)
        without modifying or truncating the full property_address / assets_location.

        Excludes: Door/plot/survey/house numbers, building names, street/road names,
                  landmarks (Opp/Near/Behind), PIN codes, and state names (unless needed).
        Hierarchy: Locality/Village -> Area/Town -> City -> District.
        """
        full_address = str(
            data.get("property_address") or
            data.get("assets_location") or
            data.get("asset_location") or
            ""
        ).strip()

        # Reject if full_address is a JSON array/object string or contains item/machinery specifications
        if full_address.startswith("[") or full_address.startswith("{") or "item:" in full_address.lower() or "make:" in full_address.lower():
            full_address = ""

        # Step 1: Check explicit schema fields (locality, village, town, city, district)
        locality = str(data.get("locality") or data.get("sub_locality") or data.get("village") or data.get("town") or "").strip()
        locality = re.sub(r"(?i)\b(village|vpo|tehsil)\b\.?\s*", "", locality).strip()

        district = str(data.get("district") or data.get("city") or data.get("city_district") or "").strip()

        derived = ""

        if locality and district and locality.lower() != district.lower():
            derived = f"{locality}, {district}"
        elif district:
            derived = district
        elif locality:
            derived = locality

        # Step 2: Fallback to parsing full_address segments if explicit fields were incomplete
        if not derived and full_address:
            # If no commas present, insert commas before known noise boundaries or landmark tokens
            clean_addr = full_address
            if "," not in clean_addr:
                clean_addr = re.sub(r"(?i)\s+(opp|near|behind|beside|adj|opposite|adjacent|gt road|g\.t\. road|street|road|st|colony|estate)\s+", ", ", clean_addr)
                clean_addr = re.sub(r"(?i)\s+(sherpur kalan|ludhiana|chennai|faridabad|guindy|rampur)\b", r", \1", clean_addr)

            # Clean newlines and split by commas
            raw_segments = [s.strip() for s in clean_addr.replace("\n", ",").split(",") if s.strip()]
            valid_segments = []

            for seg in raw_segments:
                seg_clean = seg.strip()
                # Skip numeric pin codes, pure numbers, or short noise
                if seg_clean.isdigit() or len(seg_clean) <= 2:
                    continue
                # Strip trailing state names or pin codes from segment
                seg_clean = re.sub(r"(?i)\b(punjab|tamil nadu|haryana|delhi|maharashtra|karnataka|gujarat|rajasthan|uttar pradesh|west bengal|kerala|andhra pradesh|telangana)\s*\d*$", "", seg_clean).strip()

                # Skip if segment matches any noise patterns (door/plot numbers, roads, landmarks)
                is_noise = False
                for pattern in DataNormalizer.NOISE_PATTERNS:
                    if re.search(pattern, seg_clean):
                        is_noise = True
                        break
                if not is_noise and seg_clean:
                    # Strip leading prefixes like "Village ", "VPO ", "Tehsil "
                    clean_text = re.sub(r"(?i)\b(village|vpo|tehsil)\b\.?\s*", "", seg_clean).strip()
                    valid_segments.append(clean_text)

            if len(valid_segments) >= 2:
                derived = f"{valid_segments[-2]}, {valid_segments[-1]}"
            elif len(valid_segments) == 1:
                derived = valid_segments[0]
            elif raw_segments:
                # Ultimate safe fallback from raw segments
                derived = ", ".join(raw_segments[-2:])

        # Step 3: Validation, Normalization, & Non-Location Noise Filtering
        derived = re.sub(r"\s+", " ", derived).strip()

        # Reject if derived location contains legal disclaimers, borrower names, or non-location OCR noise
        noise_location_kw = ["borrower", "notice", "description", "slno", "cpno", "guarantor", "loan", "mortgagor", "schedule", "item", "qty", "model"]
        if derived and any(nk in derived.lower() for nk in noise_location_kw):
            derived = ""

        # Filter out truncated OCR fragments like "rict", "trict", "istrict"
        if derived.lower() in {"rict", "trict", "istrict", "ct", "st"}:
            derived = ""

        # Enforce max 100 characters without truncating in the middle of a word
        if len(derived) > 100:
            parts = [p.strip() for p in derived.split(",") if p.strip()]
            reduced = ""
            for p in reversed(parts):
                candidate = f"{p}, {reduced}" if reduced else p
                if len(candidate) <= 100:
                    reduced = candidate
                else:
                    break
            if reduced:
                derived = reduced
            else:
                # Truncate at nearest space boundary before char 100
                space_idx = derived[:100].rfind(" ")
                derived = derived[:space_idx].strip() if space_idx > 0 else derived[:100].strip()

        # Step 4: Diagnostic Debug Logging
        logger.info(
            "\n[PRODUCT LOCATION DERIVATION]\n"
            "Original Address        : %s\n"
            "Derived Product Location: %s\n"
            "Length                  : %d characters",
            full_address,
            derived,
            len(derived),
        )

        return derived

    @staticmethod
    def detect_legal_event_type(data: Dict[str, Any]) -> str:
        """
        Analyze document text and extracted metadata to detect legal event type context:
        - Never uses headings like 'Sale Notice', 'E-Auction', 'Auction Notice' as event_type.
        - Analyzes legal notice text for keywords:
            - 'SARFAESI' / 'Securitisation and Reconstruction' -> 'SARFAESI ACT'
            - 'DRT' / 'Debt Recovery Tribunal' -> 'DRT'
            - 'NCLT' / 'Insolvency' -> 'NCLT'
            - 'REPO' / 'Repossessed' -> 'REPO'
            - Default -> 'SARFAESI ACT'
        """
        raw_event = str(data.get("event_type") or "").strip()
        full_text = str(
            data.get("description") or
            data.get("auction_details") or
            data.get("remarks") or
            data.get("property_address") or
            ""
        ).strip().upper()

        invalid_headings = {"sale notice", "e-auction", "eauction", "auction notice", "public notice", "notice", "sale"}
        if raw_event.lower() in invalid_headings:
            raw_event = ""

        if raw_event:
            rev_upper = raw_event.upper()
            if "SARFAESI" in rev_upper or "SECURITISATION" in rev_upper:
                return "SARFAESI ACT"
            if "DRT" in rev_upper or "DEBT RECOVERY" in rev_upper:
                return "DRT"
            if "NCLT" in rev_upper or "INSOLVENCY" in rev_upper:
                return "NCLT"
            if "REPO" in rev_upper:
                return "REPO"
            if "CONSUMER" in rev_upper or "SELLER" in rev_upper:
                return "CONSUMER/SELLER"

        if "SARFAESI" in full_text or "SECURITISATION" in full_text or "SECURITY INTEREST" in full_text:
            return "SARFAESI ACT"
        if "DRT" in full_text or "DEBT RECOVERY TRIBUNAL" in full_text:
            return "DRT"
        if "NCLT" in full_text or "INSOLVENCY" in full_text or "COMPANY LAW" in full_text:
            return "NCLT"
        if "REPO" in full_text or "REPOSSESSED" in full_text:
            return "REPO"

        return "SARFAESI ACT"

    @staticmethod
    def normalize_schema(schema: Dict[str, Any], lot_index: int = 1) -> Dict[str, Any]:
        """
        Produce a normalized clean copy of CommonAISchema.
        Preserves non-empty values and prevents writing 'null' string defaults.
        """
        from app.services.extractor.canonical_normalizer import CanonicalAliasNormalizer
        norm_schema_data = CanonicalAliasNormalizer.normalize_record_aliases(schema)
        norm: Dict[str, Any] = dict(norm_schema_data)

        from app.services.integration.payload_sanitizer import sanitize_string_field

        def clean_str(val: Any, default: str = "") -> str:
            if val is None:
                return default
            sanitized = sanitize_string_field(val)
            if not sanitized or sanitized.lower() in {"none", "null", "undefined", "n/a"}:
                return default
            return DataNormalizer.restore_legal_abbreviations(sanitized)

        # 2. Helper: Clean Monetary Strings
        def clean_money(val: Any, default: str = "") -> str:
            if val is None:
                return default
            if isinstance(val, (int, float)):
                if val == 0:
                    return default
                return f"{int(val)}" if float(val).is_integer() else f"{val:.2f}"
            raw = clean_str(val)
            if not raw or raw in {"0", "0.0", "0.00"}:
                return default
            # Strip currency prefixes (Rs., RS., INR, Rupees, ₹) and trailing '/-'
            s = re.sub(r"(?i)\b(rs|inr|rupees)\b\.?\s*", "", raw)
            s = s.replace("₹", "").replace("Rs", "").replace("rs", "").strip()
            if s.endswith("/-") or s.endswith("-"):
                s = s.rstrip("/-").strip()
            s = s.replace(",", "")

            clean = re.sub(r"[^\d.]", "", s)
            if clean:
                try:
                    flt = float(clean)
                    if flt == 0:
                        return default
                    return f"{int(flt)}" if flt.is_integer() else f"{flt:.2f}"
                except ValueError:
                    pass
            return default

        # 3. Helper: Format Clean Date (YYYY-MM-DD)
        def clean_date(val: Any, default: str = "") -> str:
            if not val:
                return default
            if isinstance(val, datetime):
                return val.strftime("%Y-%m-%d")
            val_str = clean_str(val)
            if not val_str or val_str.startswith("0000"):
                return default
            try:
                import dateutil.parser
                dt = dateutil.parser.parse(val_str)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
            return val_str

        # 3b. Helper: Format Clean DateTime (YYYY-MM-DD HH:MM:SS)
        def clean_datetime(val: Any, default: str = "") -> str:
            if not val:
                return default
            if isinstance(val, datetime):
                return val.strftime("%Y-%m-%d %H:%M:%S")
            val_str = clean_str(val)
            if not val_str or val_str.startswith("0000"):
                return default
            try:
                import dateutil.parser
                dt = dateutil.parser.parse(val_str)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
            return val_str

        # 4. Helper: Map Yes/No Flags
        def clean_flag(val: Any, default: str = "N") -> str:
            s = clean_str(val).lower()
            if not s:
                return default
            if s in {"yes", "y", "true", "1", "required"}:
                return "Y"
            if s in {"no", "n", "false", "0", "not required"}:
                return "N"
            return default

        # Apply normalizations
        norm["auction_number"] = clean_str(norm.get("auction_number")) or str(lot_index).zfill(2)
        norm["auction_date"] = clean_date(norm.get("auction_date") or (str(norm.get("auction_start_datetime")).split()[0] if norm.get("auction_start_datetime") else ""))
        norm["p_auction_date"] = norm["auction_date"]
        norm["auction_start_datetime"] = clean_datetime(norm.get("auction_start_datetime") or norm.get("auction_date_time"))
        norm["auction_end_datetime"] = clean_datetime(norm.get("auction_end_datetime") or norm.get("auction_end_date_time"))
        norm["inspection_from_date"] = clean_datetime(norm.get("inspection_from_date"))
        norm["inspection_to_date"] = clean_datetime(norm.get("inspection_to_date"))
        norm["submit_application"] = clean_datetime(norm.get("submit_application"))
        norm["catalogue_view_date"] = clean_date(norm.get("catalogue_view_date"))

        rp_clean = clean_money(norm.get("reserve_price") or norm.get("reserver_price"))
        norm["reserve_price"] = rp_clean
        norm["reserver_price"] = rp_clean

        inc_clean = clean_money(norm.get("increment_price") or norm.get("bid_increment"))
        norm["increment_price"] = inc_clean
        norm["bid_increment"] = inc_clean

        emd_clean = clean_money(norm.get("emd_amount") or norm.get("emd_price") or norm.get("pre_bid_emd"))
        norm["emd_amount"] = emd_clean
        norm["emd_price"] = emd_clean
        norm["pre_bid_emd"] = emd_clean

        norm["full_payment_balance"] = clean_money(norm.get("full_payment_balance"))
        norm["start_floor_price"] = clean_money(norm.get("start_floor_price"))

        raw_b = clean_str(norm.get("borrower_name") or norm.get("borrower") or norm.get("borrower_details") or "")
        clean_b, b_addr = DataNormalizer.separate_borrower_name_and_address(raw_b)
        norm["borrower_name"] = clean_b if clean_b else DataNormalizer.restore_legal_abbreviations(clean_str(norm.get("borrower_name"), default=""))

        if b_addr:
            current_addr = clean_str(norm.get("property_address") or norm.get("asset_location") or "")
            if not current_addr:
                norm["property_address"] = b_addr
                norm["asset_location"] = b_addr
            elif b_addr.lower() not in current_addr.lower():
                norm["property_address"] = f"{b_addr}, {current_addr}"
                norm["asset_location"] = norm["property_address"]

        norm["seller_name"] = DataNormalizer.restore_legal_abbreviations(clean_str(norm.get("seller_name")))
        norm["asset_location"] = clean_str(norm.get("asset_location") or norm.get("property_address"))
        norm["description"] = DataNormalizer.restore_legal_abbreviations(clean_str(norm.get("description")))

        norm["auto_extension"] = clean_flag(norm.get("auto_extension"), default="N")
        norm["first_bid_acceptance_condition"] = clean_str(norm.get("first_bid_acceptance_condition"), default="YES")
        norm["currency"] = clean_str(norm.get("currency"), default="INR")

        norm["emd_bank_name"] = clean_str(norm.get("emd_bank_name"), default="")
        norm["emd_account_no"] = clean_str(norm.get("emd_account_no"), default="")
        norm["emd_ifsc"] = clean_str(norm.get("emd_ifsc"), default="")
        norm["authorized_officer_name"] = clean_str(norm.get("authorized_officer_name"), default="")
        norm["authorized_officer_number"] = clean_str(norm.get("authorized_officer_number"), default="")

        logger.debug("[%d] Normalized Common AI Schema values successfully", lot_index)
        return norm

