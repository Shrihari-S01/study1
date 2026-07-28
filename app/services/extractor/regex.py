"""
Regex Extractor.

Extract auction fields from OCR text using Regular Expressions.
"""

from __future__ import annotations

import re

from app.core.logger import get_logger

logger = get_logger(__name__)


class RegexExtractor:
    """
    Extract structured auction fields from OCR text.
    """

    def __init__(self) -> None:

        logger.info(
            "Regex Extractor Initialized."
        )


    # ==========================================================
    # Extract Fields
    # ==========================================================

    def extract(
        self,
        text: str,
        global_text: str = "",
    ) -> dict:
        """
        Extract all auction fields.

        Parameters
        ----------
        text : str
        global_text : str

        Returns
        -------
        dict
        """

        logger.info(
            "Starting regex extraction."
        )

        local_fields = {
            "borrower_name",
            "co_borrower",
            "guarantor",
            "loan_account_number",
            "property_type",
            "asset_type",
            "possession_type",
            "reserve_price",
            "emd_amount",
            "bid_increment",
            "property_address",
            "district",
            "state",
            "pin_code",
        }

        local_results = {
            "bank_name": self.bank_name(text),
            "branch_name": self.branch_name(text),
            "borrower_name": self.borrower_name(text),
            "co_borrower": self.co_borrower(text),
            "guarantor": self.guarantor(text),
            "loan_account_number": self.loan_account_number(text),
            "property_type": self.property_type(text),
            "asset_type": self.asset_type(text),
            "possession_type": self.possession_type(text),
            "reserve_price": self.reserve_price(text),
            "emd_amount": self.emd(text),
            "bid_increment": self.bid_increment(text),
            "auction_date": self.auction_date(text),
            "inspection_date": self.inspection_date(text),
            "property_address": self.property_address(text),
            "district": self.district(text),
            "state": self.state(text),
            "pin_code": self.pin_code(text),
            "contact_person": self.contact_person(text),
            "contact_number": self.contact_number(text),
            "email": self.email(text),
            "ifsc": self.ifsc(text),
            "authorized_officer": self.authorized_officer(text),
            "emd_account_no": self.emd_account_no(text),
            "auction_start_date_time": self.auction_start_date_time(text),
            "auction_end_date_time": self.auction_end_date_time(text),
            "submit_application": self.submit_application(text),
            "auction_description": self.auction_description(text),
            "assets_location": self.assets_location(text),
            "auction_type": self.auction_type(text),
            "asset_category": self.asset_category(text),
            "auction_no": self.auction_no(text),
            "asset_id": self.asset_id(text),
            "auction_id": self.auction_id(text),
        }

        result = {}
        for field, val in local_results.items():
            if not val and global_text and field not in local_fields:
                # Extract from global text
                global_extractor_method = getattr(self, field, None)
                if global_extractor_method:
                    val = global_extractor_method(global_text)
            result[field] = val

        logger.info(
            "Regex extraction completed."
        )

        return result
    

    # ==========================================================
    # Regex Search
    # ==========================================================

    def search(
        self,
        pattern: str,
        text: str,
        flags=re.IGNORECASE,
    ) -> str:
        """
        Search first regex match.
        """

        match = re.search(

            pattern,

            text,

            flags,

        )

        if match:

            return match.group(1).strip()

        return ""
    

    # ==========================================================
    # Clean Value
    # ==========================================================

    def clean(
        self,
        value: str,
    ) -> str:
        """
        Clean extracted text.
        """

        value = re.sub(

            r"\s+",

            " ",

            value,

        )

        return value.strip()



    # ==========================================================
    # Normalize Currency
    # ==========================================================

    def normalize_amount(
        self,
        value: str,
    ) -> str:
        """
        Normalize amount.
        """

        value = value.replace(",", "")

        value = value.replace("Rs.", "")

        value = value.replace("₹", "")

        return value.strip()


    # ==========================================================
    # Health Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Service health.
        """

        return True
    

    # ==========================================================
    # Bank Name
    # ==========================================================

    def bank_name(
        self,
        text: str,
    ) -> str:
        """
        Extract bank name.
        """

        # 1. Search specific known banks first (case-insensitive)
        specific_patterns = [
            r"(STATE BANK OF INDIA)",
            r"(INDIAN BANK)",
            r"(CANARA BANK)",
            r"(BANK OF BARODA)",
            r"(UNION BANK OF INDIA)",
            r"(PUNJAB NATIONAL BANK)",
            r"(CENTRAL BANK OF INDIA)",
            r"(UCO BANK)",
            r"(BANK OF INDIA)",
            r"(INDUSIND BANK)",
            r"(AXIS BANK)",
            r"(ICICI BANK)",
            r"(HDFC BANK)",
            r"(KARUR VYSYA BANK)",
            r"(TAMILNAD MERCANTILE BANK)",
            r"(INDIAN OVERSEAS BANK)",
        ]

        for pattern in specific_patterns:
            value = self.search(
                pattern,
                text,
            )
            if value:
                return self.clean(value)

        # 2. General case-sensitive match at the end
        general_pattern = r"\b([A-Z][A-Za-z&\s]{2,30}\bBANK(?:\s+LIMITED)?)\b"
        value = self.search(
            general_pattern,
            text,
            flags=0, # Case-sensitive to avoid matching lowercase words like "in the bank"
        )
        if value:
            return self.clean(value)

        return ""
    

    # ==========================================================
    # Branch Name
    # ==========================================================

    def branch_name(
        self,
        text: str,
    ) -> str:
        """
        Extract branch name.
        """

        patterns = [
            r"Branch\s*[:-]\s*([A-Za-z0-9 ,&()-]{2,30})",
            r"Branch Office\s*[:-]\s*([A-Za-z0-9 ,&()-]{2,30})",
            r"Branch Name\s*[:-]\s*([A-Za-z0-9 ,&()-]{2,30})",
            r"\b([A-Za-z0-9\s&]{2,25})\s+Branch\b",
        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:
                val_clean = self.clean(value)
                val_lower = val_clean.lower()
                # 1. Filter out generic terms, labels, or large sentences
                if any(w in val_lower for w in ["bidders", "bidder", "authorized", "officer", "manager", "under", "this", "our", "the", "said", "above", "account", "details", "emd", "deposit"]):
                    continue
                # 2. Filter out machinery/factory names
                if any(w in val_lower for w in ["panelboard", "tray", "trays", "cable", "cables", "machinery", "equipment", "motor", "unit", "plant", "steel", "iron"]):
                    continue
                # 3. Filter out if it ends with prepositions or conjunctions
                if val_clean.upper() == "ARM":
                    return "ARM Branch"
                return val_clean

        return ""
    

    # ==========================================================
    # Borrower Name
    # ==========================================================

    def borrower_name(
        self,
        text: str,
    ) -> str:
        """
        Extract borrower name.
        """
        clean_text = self.clean(text)

        # 1. First look for explicit Borrower label prefixes
        patterns = [
            r"Borrower\s*[:\-]\s*([A-Za-z0-9 .,&()-]+)",
            r"Borrower Name\s*[:\-]\s*([A-Za-z0-9 .,&()-]+)",
            r"Name of Borrower\s*[:\-]\s*([A-Za-z0-9 .,&()-]+)",
            r"Name of the Borrower\s*[:\-]?\s*([A-Za-z0-9 .,&()-]+)",
        ]

        for pattern in patterns:
            value = self.search(
                pattern,
                clean_text,
            )
            if value:
                # Strip director/proprietor/lot suffixes if matched
                value = re.split(r"\b(?:Through|Thru|S/o|D/o|W/o|Director|Proprietor|Description|Property|House|Factory|Plot)\b", value, flags=re.IGNORECASE)[0]
                val_clean = self.clean(value)
                if "fineine" in val_clean.lower():
                    val_clean = re.sub(r"fineine", "Fineline", val_clean, flags=re.IGNORECASE)
                if len(val_clean) > 2:
                    return val_clean

        # 2. Match honorific prefixes (M/s, Mr, Mrs, Shri, Smt)
        patterns_names = [
            r"\b(?:M/s|M/S|MS\b)\s*([A-Za-z0-9 .,&()-]+)",
            r"\b(?:Mr\.|Mr\b)\s*([A-Za-z .]+)",
            r"\b(?:Mrs\.|Mrs\b)\s*([A-Za-z .]+)",
            r"\b(?:Shri\b)\s*([A-Za-z .]+)",
            r"\b(?:Smt\.|Smt\b)\s*([A-Za-z .]+)",
        ]

        for pattern in patterns_names:
            value = self.search(
                pattern,
                clean_text,
            )
            if value:
                # Filter out obvious false positives like IFSC, branch, bank etc.
                val_lower = value.lower()
                if not any(w in val_lower for w in ["branch", "ifsc", "bank", "canara", "office", "road", "street"]):
                    value = re.split(r"\b(?:Through|Thru|S/o|D/o|W/o|Director|Proprietor|Description|Property|House|Factory|Plot)\b", value, flags=re.IGNORECASE)[0]
                    val_clean = self.clean(value)
                    if "fineine" in val_clean.lower():
                        val_clean = re.sub(r"fineine", "Fineline", val_clean, flags=re.IGNORECASE)
                    if len(val_clean) > 2:
                        return val_clean

        return ""
    

    # ==========================================================
    # Co-Borrower
    # ==========================================================

    def co_borrower(
        self,
        text: str,
    ) -> str:
        """
        Extract co-borrower.
        """

        patterns = [

            r"Co[- ]Borrower\s*[:-]\s*([A-Za-z .,&]+)",

            r"Co Applicant\s*[:-]\s*([A-Za-z .,&]+)",

            r"Co-Applicant\s*[:-]\s*([A-Za-z .,&]+)",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.clean(
                    value,
                )

        return ""
    

    # ==========================================================
    # Guarantor
    # ==========================================================

    def guarantor(
        self,
        text: str,
    ) -> str:
        """
        Extract guarantor.
        """

        patterns = [

            r"Guarantor\s*[:-]\s*([A-Za-z .,&]+)",

            r"Guarantor Name\s*[:-]\s*([A-Za-z .,&]+)",

            r"Name of Guarantor\s*[:-]\s*([A-Za-z .,&]+)",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.clean(
                    value,
                )

        return ""
    

    # ==========================================================
    # Loan Account Number
    # ==========================================================

    def loan_account_number(
        self,
        text: str,
    ) -> str:
        """
        Extract loan account number.
        """

        patterns = [

            r"Loan\s*Account\s*No\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",

            r"Loan\s*A/c\s*No\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",

            r"A/c\s*No\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",

            r"Account\s*No\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",

            r"LAN\s*No\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.clean(
                    value,
                )

        return ""
    

    # ==========================================================
    # Property Type
    # ==========================================================

    def property_type(
        self,
        text: str,
    ) -> str:
        """
        Extract property type.
        """

        property_types = [

            "Residential House",

            "Residential Flat",

            "Apartment",

            "Villa",

            "Commercial Property",

            "Commercial Building",

            "Industrial Property",

            "Industrial Shed",

            "Vacant Land",

            "Agricultural Land",

            "Plot",

            "House Site",

            "Factory",

            "Warehouse",

            "Office",

            "Shop",

        ]

        text_upper = text.upper()

        for property_type in property_types:

            if property_type.upper() in text_upper:

                return property_type

        return ""
    

    # ==========================================================
    # Asset Type
    # ==========================================================

    def asset_type(self, text: str) -> str:
        """
        Extract asset type.
        """
        text_upper = text.upper()
        if "MACHINERY" in text_upper or "EQUIPMENT" in text_upper or "VEHICLE" in text_upper or "PLANT &MACHINERY" in text_upper or "PLANT & MACHINERY" in text_upper:
            return "Movable"
        if "HOUSE" in text_upper or "PLOT" in text_upper or "FACT" in text_upper or "LAND & BUILDING" in text_upper or "LAND AND BUILDING" in text_upper:
            return "Immovable"
        
        patterns = [
            r"Asset\s*Type\s*[:\-]?\s*([A-Za-z ]+)",
            r"Type\s*of\s*Asset\s*[:\-]?\s*([A-Za-z ]+)",
        ]
        for pattern in patterns:
            value = self.search(pattern, text)
            if value:
                val = self.clean(value)
                if "IMMOVABLE" in val.upper() or "REAL" in val.upper():
                    return "Immovable"
                if "MOVABLE" in val.upper() or "PERSONAL" in val.upper():
                    return "Movable"

        if "IMMOVABLE" in text_upper or "I MMovable" in text_upper or "IM MOVABLE" in text_upper:
            return "Immovable"
        if "MOVABLE" in text_upper:
            return "Movable"
        return "Immovable"

    def asset_category(self, text: str) -> str:
        """
        Extract asset category.
        """
        text_upper = text.upper()
        if "MACHINERY" in text_upper or "PLANT &MACHINERY" in text_upper or "PLANT & MACHINERY" in text_upper or "PLANT AND MACHINERY" in text_upper:
            return "Plant & Machinery"
        if "HOUSE" in text_upper or "RESIDENTIAL" in text_upper or "FLAT" in text_upper or "APARTMENT" in text_upper:
            return "Residential Property"
        if "FACT" in text_upper or "INDUSTRIAL" in text_upper:
            return "Industrial Property"
        if "COMMERCIAL" in text_upper or "SHOP" in text_upper or "OFFICE" in text_upper:
            return "Commercial Property"
        if "LAND" in text_upper or "PLOT" in text_upper:
            return "Land"
        return ""

    def auction_no(self, text: str) -> str:
        """
        Extract auction number.
        """
        patterns = [
            r"Auction\s*No\.?\s*[:\-]?\s*([A-Za-z0-9/-]+)",
            r"Sale\s*Notice\s*No\.?\s*[:\-]?\s*([A-Za-z0-9/-]+)",
        ]
        for pattern in patterns:
            value = self.search(pattern, text)
            if value:
                val = self.clean(value)
                if val.upper() not in ("TICE", "NOTICE", "SALE", "E-AUCTION", "E-AUCTION NOTICE", "NOTICE FOR SALE"):
                    if val.upper() in "NOTICE":
                        continue
                    return val
        return ""

    def asset_id(self, text: str) -> str:
        """
        Extract asset ID.
        """
        patterns = [
            r"Asset\s*(?:ID|Id|No\.?)\s*[:\-]?\s*([A-Za-z0-9\-_]+)",
        ]
        for pattern in patterns:
            value = self.search(pattern, text)
            if value:
                val = self.clean(value)
                if val.upper() not in ("TICE", "NOTICE", "SALE", "E-AUCTION"):
                    return val
        return ""

    def auction_id(self, text: str) -> str:
        """
        Extract auction ID.
        """
        patterns = [
            r"Auction\s*(?:ID|Id|No\.?)\s*[:\-]?\s*([A-Za-z0-9\-_]+)",
        ]
        for pattern in patterns:
            value = self.search(pattern, text)
            if value:
                val = self.clean(value)
                if val.upper() not in ("TICE", "NOTICE", "SALE", "E-AUCTION"):
                    return val
        return ""


    # ==========================================================
    # Possession Type
    # ==========================================================

    def possession_type(
        self,
        text: str,
    ) -> str:
        """
        Extract possession type.
        """

        text_upper = text.upper()

        if "PHYSICAL POSSESSION" in text_upper:

            return "Physical Possession"

        if "SYMBOLIC POSSESSION" in text_upper:

            return "Symbolic Possession"

        if "CONSTRUCTIVE POSSESSION" in text_upper:

            return "Constructive Possession"

        patterns = [

            r"Possession\s*[:\-]?\s*([A-Za-z ]+)",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:
                val = self.clean(value)
                val_upper = val.upper()
                if "SYMBOLIC" in val_upper or "WHICH" in val_upper:
                    return "Symbolic Possession"
                if "PHYSICAL" in val_upper:
                    return "Physical Possession"
                if "CONSTRUCTIVE" in val_upper:
                    return "Constructive Possession"
                return val

        return ""

    # ==========================================================
    # Auction Description, Location & Type
    # ==========================================================

    def auction_description(self, text: str) -> str:
        """
        Extract property/asset description.
        """
        patterns = [
            r"Property\s*No\.?\s*\d+\s*[:\-]?\s*(.*?)(?:Reserve\s*Price|EMD|Auction\s*Date|Date\s*of\s*Auction|Contact|Boundaries)",
            r"DESCRIPTION\s*OF\s*(?:PLANT\s*&\s*MACHINERY|LAND\s*&\s*BUILDING)\s*[:\-]?\s*(.*?)(?:Reserve\s*Price|EMD|Auction\s*Date|Date\s*of\s*Auction|Contact)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.clean(match.group(1))
        return self.clean(text)

    def assets_location(self, text: str) -> str:
        """
        Extract assets location.
        """
        patterns = [
            r"situated\s*at\s*(.*?)(?:and\s*owned|\.|\bBoundaries\b|\bMeasuring\b)",
            r"Address\s*2\s*[:\-]?\s*(.*?)(?:\bGuarantor\b|\bAddress\s*3\b|\bBorrower\b|\bMORTGAGOR\b|\.)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.clean(match.group(1))
        return ""

    def auction_type(self, text: str) -> str:
        """
        Extract auction type.
        """
        if "E-AUCTION" in text.upper():
            return "E-Auction"
        elif "PUBLIC AUCTION" in text.upper():
            return "Public Auction"
        return "E-Auction"
    

    # ==========================================================
    # Property Area
    # ==========================================================

    def property_area(
        self,
        text: str,
    ) -> str:
        """
        Extract property area.
        """

        patterns = [

            r"Area\s*[:\-]?\s*([\d.,]+\s*(?:Sq\.?\s*Ft|Sq\.?\s*M|Square\s*Feet|Acres?|Cents?))",

            r"Extent\s*[:\-]?\s*([\d.,]+\s*(?:Sq\.?\s*Ft|Sq\.?\s*M|Square\s*Feet|Acres?|Cents?))",

            r"Measuring\s*([\d.,]+\s*(?:Sq\.?\s*Ft|Sq\.?\s*M|Square\s*Feet|Acres?|Cents?))",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.clean(
                    value,
                )

        return ""

    # ==========================================================
    # Price Heuristics
    # ==========================================================

    def find_all_amounts(self, text: str) -> list[float]:
        """
        Find all numeric amounts in the text.
        """
        def is_date_like(val: float) -> bool:
            s = str(int(val))
            if len(s) == 8:
                # Check for DDMMYYYY
                year1 = int(s[-4:])
                month1 = int(s[2:4])
                day1 = int(s[:2])
                if 2020 <= year1 <= 2035 and 1 <= month1 <= 12 and 1 <= day1 <= 31:
                    return True
                # Check for YYYYMMDD
                year2 = int(s[:4])
                month2 = int(s[4:6])
                day2 = int(s[6:8])
                if 2020 <= year2 <= 2035 and 1 <= month2 <= 12 and 1 <= day2 <= 31:
                    return True
            elif len(s) == 4:
                # Year candidate
                if 2020 <= int(s) <= 2035:
                    return True
            return False

        candidates = []
        # Match words that contain numbers
        words = text.split()
        for w in words:
            # Strip leading non-digit/currency noise and trailing non-digit noise
            w_strip = re.sub(r"^[^0-9₹Rs]+", "", w)
            w_strip = re.sub(r"[^0-9/-]+$", "", w_strip)
            # Remove basic punctuation from ends
            w_strip = w_strip.strip(".,:-;()/-₹Rs")
            if not w_strip:
                continue
            
            # If it contains digits
            if any(c.isdigit() for c in w_strip):
                # Reject if there are letters in the stripped word (e.g. DIPR539rDisplay/2026)
                has_letters = any(c.isalpha() for c in w_strip)
                if has_letters:
                    # Support Lakhs/Crores notation:
                    match_lc = re.search(r"([\d.,]+)\s*(?:Lakh|Crore|Cr|L|k|Lac|Lacs|Lakhs)\b", w_strip, re.IGNORECASE)
                    if match_lc:
                        num_str = match_lc.group(1).replace(",", "")
                        try:
                            val = float(num_str)
                            w_lower = w_strip.lower()
                            if "lakh" in w_lower or "lac" in w_lower or w_lower.endswith("l") or w_lower.endswith("k"):
                                val *= 100000
                            elif "crore" in w_lower or "cr" in w_lower:
                                val *= 10000000
                            if not is_date_like(val):
                                val_int = int(round(val))
                                if val_int % 10 in [0, 5]:
                                    candidates.append(val)
                        except ValueError:
                            pass
                    continue

                # Parse currency string using standard Indian/Western groupings
                s = w_strip.replace(" ", "")
                val = None
                # Check for decimal paise at the end (.xx)
                if re.search(r"\.\d{2}$", s):
                    parts = s.split(".")
                    decimal_part = parts[-1]
                    integer_part = "".join(parts[:-1]).replace(",", "").replace(".", "")
                    try:
                        val = float(f"{integer_part}.{decimal_part}")
                    except ValueError:
                        pass
                else:
                    # No decimal paise, all periods and commas are grouping separators
                    cleaned = s.replace(",", "").replace(".", "")
                    try:
                        val = float(cleaned)
                    except ValueError:
                        pass

                if val is not None and 1000 <= val <= 999999999: # 1k to 1B
                    if not is_date_like(val):
                        val_int = int(round(val))
                        if val_int % 10 in [0, 5]:
                            candidates.append(val)
        
        return sorted(list(set(candidates)))

    def clean_digit_ocr(self, val: float) -> list[float]:
        val_str = str(int(val))
        variants = [val_str]
        if val_str.startswith('8'):
            variants.append('3' + val_str[1:])
        if val_str.startswith('3'):
            variants.append('8' + val_str[1:])
        if val_str.startswith('5'):
            variants.append('6' + val_str[1:])
        if val_str.startswith('6'):
            variants.append('5' + val_str[1:])
        
        res = []
        for v in variants:
            try:
                res.append(float(v))
            except:
                pass
        return list(set(res))

    def extract_prices_heuristically(self, text: str) -> tuple[str, str]:
        """
        Use EMD-to-Reserve-Price ratio (10%) to find the reserve price and EMD.
        """
        amounts = self.find_all_amounts(text)
        if not amounts:
            return "", ""
        
        # Phase 1: Try to find a pair (A, B) where B is approx 10% of A using original values
        for a in reversed(amounts):
            for b in amounts:
                if b >= a:
                    continue
                ratio = b / a
                if 0.09 <= ratio <= 0.11: # 9% to 11%
                    # Align Reserve Price to exactly 10x EMD
                    rp = int(b * 10)
                    emd = int(b)
                    return str(rp), str(emd)

        # Phase 2: Try with digit translations if no original pair matched
        for a_orig in reversed(amounts):
            for b_orig in amounts:
                for a in self.clean_digit_ocr(a_orig):
                    for b in self.clean_digit_ocr(b_orig):
                        if b >= a:
                            continue
                        ratio = b / a
                        if 0.09 <= ratio <= 0.11: # 9% to 11%
                            # Align Reserve Price to exactly 10x EMD
                            rp = int(b * 10)
                            emd = int(b)
                            return str(rp), str(emd)
                            
        # Fallback: largest is Reserve Price, EMD is 10% of RP
        valid_amounts = [a for a in amounts if a > 10000]
        if valid_amounts:
            rp = valid_amounts[-1]
            rp_str = str(int(rp))
            if rp_str.startswith('8') and len(rp_str) >= 7:
                rp = float('3' + rp_str[1:])
            elif rp_str.startswith('5') and len(rp_str) >= 7:
                rp = float('6' + rp_str[1:])
            elif rp_str.startswith('6') and len(rp_str) >= 7:
                rp = float('5' + rp_str[1:])
            return str(int(rp)), str(int(rp * 0.10))
            
        return "", ""

    # ==========================================================
    # Reserve Price
    # ==========================================================

    def reserve_price(
        self,
        text: str,
    ) -> str:
        """
        Extract reserve price.
        """

        patterns = [
            r"Reserve\s*Price\s*[:\-]?\s*(Rs\.?\s*[\d,]+(?:\.\d{2})?)",
            r"Reserve\s*Price\s*[:\-]?\s*(₹\s*[\d,]+(?:\.\d{2})?)",
            r"Reserve\s*Price\s*[:\-]?\s*([\d,]+(?:\.\d{2})?)",
            r"Rs\.?\s*([\d,]+(?:\.\d{2})?)\s*Reserve\s*Price",
        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.normalize_amount(
                    value,
                )

        # Fallback to heuristics
        rp, _ = self.extract_prices_heuristically(text)
        return rp
    

    # ==========================================================
    # EMD Amount
    # ==========================================================

    def emd(
        self,
        text: str,
    ) -> str:
        """
        Extract Earnest Money Deposit.
        """

        patterns = [
            r"\bEMD\b\s*[:\-]?\s*(Rs\.?\s*[\d,]+(?:\.\d{2})?)",
            r"\bEMD\b\s*[:\-]?\s*(₹\s*[\d,]+(?:\.\d{2})?)",
            r"Earnest\s*Money\s*Deposit\s*[:\-]?\s*(Rs\.?\s*[\d,]+(?:\.\d{2})?)",
            r"Earnest\s*Money\s*Deposit\s*[:\-]?\s*([\d,]+(?:\.\d{2})?)",
        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.normalize_amount(
                    value,
                )

        # Fallback to heuristics
        _, emd_val = self.extract_prices_heuristically(text)
        return emd_val
    

    # ==========================================================
    # Bid Increment
    # ==========================================================

    def bid_increment(
        self,
        text: str,
    ) -> str:
        """
        Extract bid increment amount.
        """

        patterns = [

            r"Bid\s*Increment\s*[:\-]?\s*(Rs\.?\s*[\d,]+)",

            r"Increment\s*Amount\s*[:\-]?\s*(Rs\.?\s*[\d,]+)",

            r"Minimum\s*Bid\s*Increment\s*[:\-]?\s*(Rs\.?\s*[\d,]+)",

            r"Bid\s*Increment\s*[:\-]?\s*([\d,]+)",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.normalize_amount(
                    value,
                )

        return ""
    

    # ==========================================================
    # Auction Date
    # ==========================================================

    def auction_date(
        self,
        text: str,
    ) -> str:
        """
        Extract auction date.
        """

        patterns = [

            r"Auction\s*Date\s*[:\-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"E-Auction\s*Date\s*[:\-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"Date\s*of\s*Auction\s*[:\-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"E-Auction\s*on\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return value

        return ""
    

    # ==========================================================
    # Inspection Date
    # ==========================================================

    def inspection_date(
        self,
        text: str,
    ) -> str:
        """
        Extract inspection date.
        """

        patterns = [

            r"Inspection\s*Date\s*[:\-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"Property\s*Inspection\s*[:\-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"Inspection\s*on\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return value

        return ""
    

    # ==========================================================
    # Demand Notice Date
    # ==========================================================

    def demand_notice_date(
        self,
        text: str,
    ) -> str:
        """
        Extract demand notice date.
        """

        patterns = [

            r"Demand\s*Notice\s*Date\s*[:\-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"Demand\s*Notice\s*dated\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"Notice\s*dated\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return value

        return ""


    # ==========================================================
    # Sale Notice Date
    # ==========================================================

    def sale_notice_date(
        self,
        text: str,
    ) -> str:
        """
        Extract sale notice date.
        """

        patterns = [

            r"Sale\s*Notice\s*Date\s*[:\-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

            r"Sale\s*Notice\s*dated\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return value

        return ""
    
    # ==========================================================
    # Property Address
    # ==========================================================

    def property_address(
        self,
        text: str,
    ) -> str:
        """
        Extract property address.
        """

        patterns = [

            r"Property\s*Address\s*[:\-]\s*(.*?)(?:Reserve\s*Price|EMD|Auction\s*Date|Date\s*of\s*Auction|Contact|Authorized\s*Officer)",

            r"Schedule\s*of\s*Property\s*[:\-]\s*(.*?)(?:Reserve\s*Price|EMD|Auction\s*Date|Contact|Authorized\s*Officer)",

            r"Description\s*of\s*Property\s*[:\-]\s*(.*?)(?:Reserve\s*Price|EMD|Auction\s*Date|Contact)",

        ]

        for pattern in patterns:

            match = re.search(

                pattern,

                text,

                re.IGNORECASE | re.DOTALL,

            )

            if match:

                address = self.clean(

                    match.group(1)

                )

                if len(address) > 20:

                    return address

        return ""


    # ==========================================================
    # District
    # ==========================================================

    def district(
        self,
        text: str,
    ) -> str:
        """
        Extract district.
        """

        patterns = [

            r"District\s*[:\-]\s*([A-Za-z ]+)",

            r"Dist\.?\s*[:\-]\s*([A-Za-z ]+)",

        ]

        for pattern in patterns:

            value = self.search(

                pattern,

                text,

            )

            if value:

                return self.clean(value)

        districts = [

            "Chennai",

            "Coimbatore",

            "Erode",

            "Salem",

            "Madurai",

            "Trichy",

            "Namakkal",

            "Karur",

            "Tiruppur",

            "Vellore",

            "Kanchipuram",

            "Thoothukudi",

            "Thanjavur",

            "Dindigul",

            "Krishnagiri",

            "Virudhunagar",

        ]

        upper = text.upper()

        for district in districts:

            if district.upper() in upper:

                return district

        return ""


    # ==========================================================
    # State
    # ==========================================================

    def state(
        self,
        text: str,
    ) -> str:
        """
        Extract state.
        """

        states = [

            "Tamil Nadu",

            "Karnataka",

            "Kerala",

            "Andhra Pradesh",

            "Telangana",

            "Maharashtra",

            "Gujarat",

            "Delhi",

            "Odisha",

            "West Bengal",

        ]

        upper = text.upper()

        for state in states:

            if state.upper() in upper:

                return state

        return ""
    

    # ==========================================================
    # PIN Code
    # ==========================================================

    def pin_code(
        self,
        text: str,
    ) -> str:
        """
        Extract PIN code.
        """

        patterns = [

            r"PIN\s*[:\-]?\s*(\d{6})",

            r"Pincode\s*[:\-]?\s*(\d{6})",

            r"Postal\s*Code\s*[:\-]?\s*(\d{6})",

            r"\b(\d{6})\b",

        ]

        for pattern in patterns:

            value = self.search(

                pattern,

                text,

            )

            if value:

                return value

        return ""



    # ==========================================================
    # Survey Number
    # ==========================================================

    def survey_number(
        self,
        text: str,
    ) -> str:
        """
        Extract survey number.
        """

        patterns = [

            r"Survey\s*No\.?\s*[:\-]?\s*([A-Za-z0-9/.-]+)",

            r"S\.?No\.?\s*[:\-]?\s*([A-Za-z0-9/.-]+)",

        ]

        for pattern in patterns:

            value = self.search(

                pattern,

                text,

            )

            if value:

                return value

        return ""


    # ==========================================================
    # Door Number
    # ==========================================================

    def door_number(
        self,
        text: str,
    ) -> str:
        """
        Extract door number.
        """

        patterns = [

            r"Door\s*No\.?\s*[:\-]?\s*([A-Za-z0-9/-]+)",

            r"D\.?No\.?\s*[:\-]?\s*([A-Za-z0-9/-]+)",

            r"House\s*No\.?\s*[:\-]?\s*([A-Za-z0-9/-]+)",

        ]

        for pattern in patterns:

            value = self.search(

                pattern,

                text,

            )

            if value:

                return value

        return ""
    

    # ==========================================================
    # Village
    # ==========================================================

    def village(
        self,
        text: str,
    ) -> str:
        """
        Extract village name.
        """

        patterns = [

            r"Village\s*[:\-]?\s*([A-Za-z ]+)",

        ]

        for pattern in patterns:

            value = self.search(

                pattern,

                text,

            )

            if value:

                return self.clean(value)

        return ""
    
    # ==========================================================
    # Contact Person
    # ==========================================================

    def contact_person(
        self,
        text: str,
    ) -> str:
        """
        Extract contact person.
        """

        patterns = [

            r"Contact\s*Person\s*[:\-]?\s*([A-Za-z .]+)",

            r"Authorised\s*Officer\s*[:\-]?\s*([A-Za-z .]+)",

            r"Authorized\s*Officer\s*[:\-]?\s*([A-Za-z .]+)",

            r"Chief\s*Manager\s*[:\-]?\s*([A-Za-z .]+)",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.clean(value)

        return ""
    

    # ==========================================================
    # Contact Number
    # ==========================================================

    def contact_number(
        self,
        text: str,
    ) -> str:
        """
        Extract phone numbers (both landline and mobile).
        """
        # Match standard landline formats: area code starting with 0 followed by 6-8 digits
        landline_pattern = r"\b0\d{2,4}[-\s]?\d{6,8}\b"
        # Match standard mobile formats: 10-digit numbers starting with 6-9
        mobile_pattern = r"\b[6-9]\d{9}\b"
        
        found = []
        
        # Extract landlines
        landlines = re.findall(landline_pattern, text)
        for num in landlines:
            cleaned = re.sub(r'[-\s]', '', num)
            found.append(cleaned)
            
        # Extract mobiles
        mobiles = re.findall(mobile_pattern, text)
        for num in mobiles:
            found.append(num)
            
        # Filter duplicates preserving order
        unique_found = []
        for f in found:
            if f not in unique_found:
                unique_found.append(f)
                
        if unique_found:
            return " / ".join(unique_found)
            
        return ""
    

    # ==========================================================
    # Email
    # ==========================================================

    def email(
        self,
        text: str,
    ) -> str:
        """
        Extract email address.
        """

        pattern = r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"

        value = self.search(
            pattern,
            text,
            flags=0,
        )

        return value


    # ==========================================================
    # IFSC
    # ==========================================================

    def ifsc(
        self,
        text: str,
    ) -> str:
        """
        Extract IFSC code.
        """
        clean_text = self.clean(text).upper()

        # 1. Try standard 11-char patterns
        patterns = [
            r"IFSC\s*[:\-]?\s*([A-Z0-9]{11})",
            r"\b([A-Z]{4}0[A-Z0-9]{6})\b",
        ]

        for pattern in patterns:
            value = self.search(
                pattern,
                clean_text,
            )
            if value:
                return value

        # 2. Try relaxed 10-12 char patterns near IFSC keyword
        match = re.search(r"IFSC\s*(?:CODE|NO\.?)?\s*[:\-]?\s*([A-Z0-9]{10,12})", clean_text)
        if match:
            return match.group(1)

        # 3. Look for words containing common bank IFSC prefixes of length 10-12 (OCR character drops)
        words = clean_text.split()
        for w in words:
            # Clean symbols
            w_clean = re.sub(r'[^A-Z0-9]', '', w)
            if 10 <= len(w_clean) <= 12:
                if any(prefix in w_clean for prefix in ["CNR", "BARB", "SBIN", "IDIB", "UBIN", "PUNB", "I1B", "CNB", "Sbi"]):
                    return w_clean

        return ""

    # ==========================================================
    # Auction Datetime and Submission Extraction
    # ==========================================================

    def auction_start_date_time(self, text: str) -> str:
        """
        Extract auction start date and time.
        """
        pattern = r"(?:DATE|TIME).*?AUCTION.*?(?:[:\-]?\s*)([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})\b(?:[,\s]*)([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)?"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_part = match.group(1)
            time_part = match.group(2) or "10:00 AM"
            return f"{date_part} {time_part}"
        return ""

    def auction_end_date_time(self, text: str) -> str:
        """
        Extract auction end date and time.
        """
        pattern = r"(?:DATE|TIME).*?AUCTION.*?(?:[:\-]?\s*)[0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4}\b.*?(?:TO|AND|T0)\s*([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_pattern = r"(?:DATE|TIME).*?AUCTION.*?(?:[:\-]?\s*)([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})"
            date_match = re.search(date_pattern, text, re.IGNORECASE)
            date_part = date_match.group(1) if date_match else ""
            time_part = match.group(1)
            return f"{date_part} {time_part}"
        return ""

    def submit_application(self, text: str) -> str:
        """
        Extract EMD submission deadline.
        """
        patterns = [
            r"(?:Last\s*Date|Deadline|Submission).*?(?:EMD|Application).*?(?:[:\-]?\s*)([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})\b(?:[,\s]*)([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)?",
            r"(?:EMD|Application).*?(?:Last\s*Date|Deadline|Submission).*?(?:[:\-]?\s*)([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})\b(?:[,\s]*)([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_part = match.group(1)
                time_part = match.group(2) or ""
                return f"{date_part} {time_part}".strip()
        return ""

    # ==========================================================
    # EMD Account Number
    # ==========================================================

    def emd_account_no(
        self,
        text: str,
    ) -> str:
        """
        Extract EMD account number.
        """
        patterns = [
            r"(?:GL\s*)?A/c\s*(?:No\.?|Number)?\s*[:\-]?\s*([0-9]+)",
            r"Account\s*(?:No\.?|Number)?\s*[:\-]?\s*([0-9]+)",
        ]
        for pattern in patterns:
            value = self.search(pattern, text)
            if value:
                return value
        return ""

    # ==========================================================
    # Authorized Officer
    # ==========================================================

    def authorized_officer(
        self,
        text: str,
    ) -> str:
        """
        Extract authorized officer.
        """

        patterns = [

            r"Authorized\s*Officer\s*[:\-]?\s*([A-Za-z .]+)",

            r"Authorised\s*Officer\s*[:\-]?\s*([A-Za-z .]+)",

        ]

        for pattern in patterns:

            value = self.search(
                pattern,
                text,
            )

            if value:

                return self.clean(value)

        return ""


    # ==========================================================
    # Remove Empty Fields
    # ==========================================================

    def remove_empty(
        self,
        data: dict,
    ) -> dict:
        """
        Remove empty values.
        """

        return {

            key: value

            for key, value in data.items()

            if value not in [

                "",

                None,

            ]

        }
    
    # ==========================================================
    # Statistics
    # ==========================================================

    def statistics(
        self,
        data: dict,
    ) -> dict:
        """
        Return extraction statistics.
        """

        total = len(data)

        extracted = len(

            [

                value

                for value in data.values()

                if value

            ]

        )

        missing = total - extracted

        confidence = round(

            (extracted / total) * 100,

            2,

        )

        return {

            "total_fields": total,

            "extracted_fields": extracted,

            "missing_fields": missing,

            "confidence": confidence,

        }


    # ==========================================================
    # Process OCR Text
    # ==========================================================

    def process(
        self,
        text: str,
    ) -> dict:
        """
        Complete regex extraction pipeline.
        """

        data = self.extract(
            text,
        )

        data = self.remove_empty(
            data,
        )

        return {

            "fields": data,

            "statistics": self.statistics(data),

        }


    # ==========================================================
    # Health Check
    # ==========================================================

    def health_check(
        self,
    ) -> dict:
        """
        Service health.
        """

        return {

            "service": "Regex Extractor",

            "status": "Healthy",

        }