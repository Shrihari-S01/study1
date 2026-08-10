"""
Document Classifier for PDF Auction Catalogues.
Classifies input documents into catalogue domains (MSTC, Metaljunction, LIC Housing, Bank Auction, Government, Generic).
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)

class DocumentClassifier:
    """
    Classifies PDF document layout type based on structural headers and keywords.
    """

    def classify(self, text: str) -> str:
        """
        Determine document type from extracted raw text.
        """
        if not text:
            return "generic"

        t_upper = text.upper()

        # 1. MSTC Catalogue
        if "MSTC" in t_upper or "DETAILED AUCTION CATALOGUE" in t_upper or "MSTC OFFICER DETAILS" in t_upper:
            logger.info("Document Classified: MSTC Catalogue")
            return "mstc"

        # 2. Metaljunction Catalogue
        if "METALJUNCTION" in t_upper or "MJJUNCTION" in t_upper or "VALUEJUNCTION" in t_upper:
            logger.info("Document Classified: Metaljunction Catalogue")
            return "metaljunction"

        # 3. LIC Housing Finance
        if "LIC HOUSING" in t_upper or "LICHFL" in t_upper:
            logger.info("Document Classified: LIC Housing Finance Notice")
            return "lic_housing"

        # 4. Bank Auction Notice (SARFAESI)
        if "SARFAESI" in t_upper or "SECURITY INTEREST" in t_upper or "AUTHORISED OFFICER" in t_upper or "RESERVE PRICE" in t_upper:
            logger.info("Document Classified: Bank Auction Notice")
            return "bank_auction"

        # 5. Government Catalogue / Tender
        if "GOVERNMENT OF INDIA" in t_upper or "TENDER NOTICE" in t_upper or "PUBLIC AUCTION" in t_upper:
            logger.info("Document Classified: Government Catalogue")
            return "government"

        logger.info("Document Classified: Generic Auction Catalogue")
        return "generic"
