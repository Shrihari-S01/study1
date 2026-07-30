"""
Seller Parser for PDF Auction Processing Pipeline.
Extracts seller details, seller address, contact person, email, and phone.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class SellerParser:
    """
    Extracts seller organization details from the Seller section.
    """

    def parse_seller(self, text: str) -> dict:
        """
        Extract seller information dict.
        """
        seller_data = {
            "institution_seller": None,
            "seller_address": None,
            "contact_person": None,
            "telephone_number": None,
            "seller_email": None
        }

        if not text:
            return seller_data

        # 1. Seller Name / Institution Seller (Excludes "Details:")
        name_m = re.search(r'(?i)(?:Seller\s+Name|Institution\s+Name|Name\s+of\s+Seller|Beneficiary\s+Name/Payment\s+favoring)\s*[:.-]?\s*([^\n]+)', text)
        if name_m:
            val = name_m.group(1).strip()
            if val and val.lower() not in ("details:", "details", "name"):
                seller_data["institution_seller"] = val

        if not seller_data["institution_seller"]:
            # Fallback for plain "Seller Name MAHINDRA MSTC RECYCLING PRIVATE LIMITED"
            mstc_s = re.search(r'(?i)(?:MAHINDRA\s+MSTC[^\n]+)', text)
            if mstc_s:
                seller_data["institution_seller"] = mstc_s.group(0).strip()

        # 2. Seller Address
        addr_m = re.search(r'(?i)(?:Seller\s+Address|Address\s+of\s+Seller|Location)\s*[:.-]?\s*([^\n]+(?:\n[^\n]+)?)', text)
        if addr_m:
            seller_data["seller_address"] = addr_m.group(1).strip()

        # 3. Contact Person
        c_m = re.search(r'(?i)(?:Contact\s+Person|Contact\s+Name|Authorized\s+Person)\s*[:.-]?\s*([^\n]+)', text)
        if c_m:
            seller_data["contact_person"] = c_m.group(1).strip()

        # 4. Telephone Number / Phone
        p_m = re.search(r'(?i)(?:Telephone\s+Number|Phone|Mobile|Contact\s+Number)\s*[:.-]?\s*([0-9\s/,-]{8,25})', text)
        if p_m:
            seller_data["telephone_number"] = p_m.group(1).strip()

        # 5. Email Address
        e_m = re.search(r'(?i)(?:Seller\s+Email\s+Address|Email|E-mail)\s*[:.-]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        if e_m:
            seller_data["seller_email"] = e_m.group(1).strip()

        logger.info("Seller Details Extracted (Institution Seller: %s, Contact: %s).",
                    seller_data.get("institution_seller"), seller_data.get("contact_person"))

        return seller_data
