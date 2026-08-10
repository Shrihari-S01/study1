"""
Officer Parser for PDF Auction Processing Pipeline.
Extracts officer names, designations, email addresses, and phone numbers.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)

class OfficerParser:
    """
    Extracts Authorized Officer / Officer details from the Officer Section.
    """

    def parse_officer(self, text: str) -> dict:
        """
        Extract officer details dict.
        """
        officer_data = {
            "authorized_officer_name": None,
            "authorized_officer_number": None,
            "officer_email": None
        }

        if not text:
            return officer_data

        # 1. Primary Officer (Name & Designation of Officer One / Two / Authorized Officer)
        officer_matches = re.findall(r'(?i)(?:Name\s+&\s+Designation\s+of\s+Officer\s+[A-Za-z]+|Authorized\s+Officer|Authorised\s+Officer|Contact\s+Person)\s*[:.-]?\s*(?:Name:\s*)?([^\n\-\[]+)', text)
        if officer_matches:
            clean_names = [name.strip() for name in officer_matches if name.strip() and "helpdesk" not in name.lower()]
            if clean_names:
                officer_data["authorized_officer_name"] = clean_names[0]

        # 2. Officer Phone Numbers
        phones = re.findall(r'\b\d{10}\b', text)
        if phones:
            officer_data["authorized_officer_number"] = " / ".join(phones[:3])

        # 3. Officer Email
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if emails:
            officer_data["officer_email"] = emails[0]

        logger.info("Officer Details Extracted (Name: %s, Number: %s).",
                    officer_data.get("authorized_officer_name"), officer_data.get("authorized_officer_number"))

        return officer_data
