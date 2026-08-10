"""
PDF Parser Service - Master Entry Point for PDF Processing Pipeline (Version 2.0).
Routes processing through Stages 1 to 16 PDFPipeline engine.
"""

from app.core.logger import get_logger
from app.services.pdf.pdf_pipeline import PDFPipeline

logger = get_logger(__name__)

class PDFParserService:
    """
    Entry point service for PDF Auction Processing Pipeline Version 2.0.
    """

    def __init__(self) -> None:
        logger.info("Initializing PDF Parser Service Version 2.0.")
        self.pipeline = PDFPipeline()

    def process_pdf_file(self, pdf_path: str, ocr_service=None) -> dict:
        """
        Delegate PDF execution to PDFPipeline (Stages 1 - 16).
        """
        logger.info("Routing file to PDFPipeline Version 2.0: %s", pdf_path)
        return self.pipeline.run_pipeline(pdf_path, ocr_service=ocr_service)
