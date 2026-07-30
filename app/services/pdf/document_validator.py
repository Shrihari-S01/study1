"""
Document Validator for PDF Auction Processing Pipeline (Stage 1).
Validates readability, page count, text layer availability, encryption, and corruption.
"""

from __future__ import annotations
import fitz  # PyMuPDF
from app.core.logger import get_logger

logger = get_logger(__name__)


class DocumentValidator:
    """
    Stage 1: Validates incoming PDF files prior to parsing.
    """

    def validate_pdf(self, pdf_path: str) -> dict:
        """
        Validate readability, page counts, text layer availability, encryption, and corruption.
        """
        result = {
            "is_valid": True,
            "page_count": 0,
            "has_text_layer": False,
            "is_encrypted": False,
            "errors": []
        }

        try:
            doc = fitz.open(pdf_path)
            result["page_count"] = len(doc)

            if doc.is_encrypted:
                result["is_encrypted"] = True
                result["is_valid"] = False
                result["errors"].append("PDF is encrypted and password-protected.")
                logger.error("Document Validation Failed: Encrypted PDF.")
                return result

            if result["page_count"] == 0:
                result["is_valid"] = False
                result["errors"].append("PDF contains 0 pages.")
                logger.error("Document Validation Failed: Empty PDF.")
                return result

            # Check text layer availability across pages
            total_text_length = 0
            for page in doc:
                text = page.get_text("text") or ""
                total_text_length += len(text.strip())

            if total_text_length > 50:
                result["has_text_layer"] = True
            else:
                logger.warning("Document Validation Notice: Low or missing native text layer (total text length: %d). OCR fallback recommended.", total_text_length)

            doc.close()
            logger.info("Stage 1 Document Validation PASSED: %d Pages, Text Layer: %s.", result["page_count"], result["has_text_layer"])

        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"Corrupted or unreadable PDF: {str(e)}")
            logger.exception("Stage 1 Document Validation Exception: %s", str(e))

        return result
