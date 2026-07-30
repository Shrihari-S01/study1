"""
Section Detector for PDF Auction Processing Pipeline.
Partitions the Document Object into logical sections (Header, Seller, Bank, Officer, Lots, Terms).
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class SectionDetector:
    """
    Detects section boundaries using structural markers, independent of page numbers.
    """

    def detect_sections(self, doc_obj: dict) -> dict:
        """
        Segment full_text into section objects.
        """
        full_text = doc_obj.get("full_text", "")
        sections = {
            "header": "",
            "seller": "",
            "bank": "",
            "officer": "",
            "lots": "",
            "terms": "",
            "footer": "",
            "annexure": ""
        }

        if not full_text:
            return sections

        lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

        # 1. Terms & Conditions Boundary
        terms_idx = len(lines)
        for i, ln in enumerate(lines):
            if re.search(r'(?i)^(?:Terms\s+and\s+Conditions|Terms\s+&\s+Conditions|Special\s+Terms|ASTC|SSTC|General\s+Terms)', ln):
                terms_idx = i
                break

        header_seller_lines = lines[:terms_idx]
        terms_lines = lines[terms_idx:]

        sections["terms"] = "\n".join(terms_lines)

        # 2. Lot Details Boundary
        lot_start_idx = len(header_seller_lines)
        for i, ln in enumerate(header_seller_lines):
            if re.search(r'(?i)^(?:Lot\s+Details|Lot\s+No\s*-|Lot\s+Number|Item\s+Details|Property\s+Details)', ln):
                lot_start_idx = i
                break

        header_lines = header_seller_lines[:lot_start_idx]
        lot_lines = header_seller_lines[lot_start_idx:]

        sections["lots"] = "\n".join(lot_lines)

        # 3. Sub-segment Header into Seller, Bank, Officer, Header
        header_text = "\n".join(header_lines)
        sections["header"] = header_text

        # Bank Account Details Section
        bank_match = re.search(r'(?i)(?:Seller\s+Account\s+Details|Beneficiary\s+Name|Payment\s+favoring|Bank\s+Account\s+Details|EMD\s+Bank\s+Details)(.*?)(?=MSTC\s+Officer|Seller\s+Details|Lot\s+Details|$)', header_text, re.DOTALL)
        if bank_match:
            sections["bank"] = bank_match.group(0).strip()
        else:
            sections["bank"] = header_text

        # Seller Details Section
        seller_match = re.search(r'(?i)(?:Seller\s+Details|Seller\s+Name|Institution\s+Name)(.*?)(?=Seller\s+Account|Beneficiary\s+Name|Officer\s+Details|Lot\s+Details|$)', header_text, re.DOTALL)
        if seller_match:
            sections["seller"] = seller_match.group(0).strip()
        else:
            sections["seller"] = header_text

        # Officer Details Section
        officer_match = re.search(r'(?i)(?:Officer\s+Details|MSTC\s+Officer\s+Details|Authorized\s+Officer|Contact\s+Person)(.*?)(?=Lot\s+Details|Terms|$)', header_text, re.DOTALL)
        if officer_match:
            sections["officer"] = officer_match.group(0).strip()
        else:
            sections["officer"] = header_text

        logger.info("Section Boundary Detection Completed (Header: %d chars, Lots: %d chars, Terms: %d chars).",
                    len(sections["header"]), len(sections["lots"]), len(sections["terms"]))

        return sections
