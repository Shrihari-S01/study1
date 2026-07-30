"""
Normalization Engine for PDF Auction Processing Pipeline (Stage 9).
Cleans categories, numbers, prices, descriptions, and auction identifiers before field mapping.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class Normalizer:
    """
    Stage 9: Normalization Engine for PDF data fields.
    """

    PARSER_ARTIFACTS = {")", "-", "0.0", "pcb group", "(", "0", "", ":"}

    def normalize_auction_number(self, raw_val: str) -> str:
        """
        Extract numeric suffix only (e.g. MSTC/.../19530 -> 19530).
        """
        if not raw_val:
            return ""
        raw_str = str(raw_val).strip()
        digits = re.findall(r'\d+', raw_str)
        if digits:
            return digits[-1]
        return raw_str

    def normalize_category(self, raw_cat: str) -> str:
        """
        Remove parser artifacts such as ')', ':', '0.0', '-' and return clean category.
        """
        if not raw_cat:
            return "Miscellaneous Items"

        clean = re.sub(r'[\)\-0-9.:\s]+$', '', str(raw_cat)).strip()
        clean = re.sub(r'^[\)\-0-9.:\s]+', '', clean).strip(' -,\t\r\n')

        if not clean or clean.lower() in self.PARSER_ARTIFACTS or len(clean) < 2:
            return "Miscellaneous Items"

        return clean

    def normalize_price(self, val) -> float | None:
        """
        Convert to numeric float preserving decimals. Return None if missing/invalid.
        """
        if val in (None, "", "0", "0.0"):
            return None
        try:
            clean_s = str(val).replace(",", "").replace("₹", "").replace("Rs.", "").strip()
            return float(clean_s)
        except Exception:
            return None

    def normalize_description(self, raw_desc: str) -> str:
        """
        Merge line breaks and strip trailing punctuation without truncating description text.
        """
        if not raw_desc:
            return ""

        clean_d = " ".join([ln.strip() for ln in str(raw_desc).splitlines() if ln.strip()])
        clean_d = re.sub(r'[\s,\-]+$', '', clean_d).strip()
        return clean_d
