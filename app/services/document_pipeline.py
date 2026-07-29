"""
Document Processing Pipeline.

Handles multi-page PDF documents.
"""

from __future__ import annotations

import base64
import io
import os
import uuid
import fitz  # PyMuPDF
from PIL import Image
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.repositories.upload_repository import UploadRepository
from app.services.upload.upload_service import UploadService
from app.services.extractor.parser import AuctionParser
from app.services.storage.database_service import DatabaseService
from app.services.ocr.paddle_service import PaddleOCRService

logger = get_logger(__name__)


class DocumentPipeline:
    """
    Document processing pipeline for multi-page PDFs.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        logger.info("Initializing Document Processing Pipeline.")
        self.db = db
        repository = UploadRepository(db)
        self.upload_service = UploadService(repository=repository)
        self.parser = AuctionParser()
        self.database = DatabaseService(db)
        self.ocr = PaddleOCRService()

    def stitch_pages(self, page_images: list[Image.Image]) -> Image.Image:
        """
        Stitch up to 4 pages into a 2x2 grid image.
        Uses standard A4 dimensions (1240 x 1754 at 150 DPI) for each cell.
        """
        W, H = 1240, 1754
        resized = [img.resize((W, H), Image.Resampling.LANCZOS) for img in page_images]

        # Create a blank white canvas for a 2x2 grid
        canvas = Image.new("RGB", (W * 2, H * 2), "white")

        # Paste up to 4 images
        positions = [(0, 0), (W, 0), (0, H), (W, H)]
        for img, pos in zip(resized, positions):
            canvas.paste(img, pos)

        return canvas

    async def run(
        self,
        file,
    ) -> dict:
        """
        Execute PDF document extraction pipeline.
        """
        logger.info("Starting Document Pipeline execution.")

        try:
            # 1. Upload and store PDF
            upload = await self.upload_service.upload_file(file)
            pdf_path = upload.original_file_path

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Uploaded PDF not found at {pdf_path}")

            # 2. Extract digital text directly from PDF preserving page numbers and table layout
            logger.info("Extracting native digital text directly from PDF document.")
            doc = fitz.open(pdf_path)
            full_pdf_text_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract page text preserving structural layout / tables
                page_text = page.get_text("text")
                full_pdf_text_parts.append(f"--- PAGE {page_num + 1} ---\n{page_text}")
            doc.close()

            full_pdf_text = "\n\n".join(full_pdf_text_parts)
            logger.info(f"Extracted digital text from {len(full_pdf_text_parts)} pages.")

            # 3. Process via Pipeline B (Section-aware PDF Catalogue Extraction)
            saved_records = []
            extraction_results = []
            total_notices = 0

            try:
                parsed = self.parser.parse_pdf_catalogue(full_pdf_text)
                records = parsed.get("fields", [])
                if isinstance(records, dict):
                    records = [records]
                elif not isinstance(records, list):
                    records = []

                # Save each lot record to database
                for record in records:
                    record["upload_id"] = upload.id
                    saved = await self.database.save_auction(record)
                    saved_records.append(saved)
                    total_notices += 1

                extraction_results.append({
                    "success": True,
                    "document": pdf_path,
                    "message": "Processed PDF catalogue successfully via Pipeline B."
                })
            except Exception as exc:
                logger.exception(f"Failed to process PDF document {pdf_path}")
                extraction_results.append({
                    "success": False,
                    "document": pdf_path,
                    "message": str(exc)
                })

            # 5. Build consolidated response
            summary = {
                "total_notices": total_notices,
                "successful": len(saved_records),
                "failed": len(stitched_images_paths) - len(saved_records) if total_notices == 0 else 0
            }

            # Update upload status in repository
            await self.upload_service.repository.update_status(
                upload=upload,
                status="COMPLETED",
            )
            await self.upload_service.repository.update_statistics(
                upload=upload,
                total_notices=total_notices,
                successful_notices=len(saved_records),
                failed_notices=summary["failed"],
                processing_time=0.0,
                confidence_score=0.99
            )

            result = {
                "upload": upload,
                "results": saved_records,
                "summary": summary,
                "extraction_results": extraction_results
            }

            return self.build_response(result)

        except Exception as exc:
            logger.exception("Document pipeline execution failed.")
            return {
                "success": False,
                "message": str(exc)
            }

    def build_response(self, result: dict) -> dict:
        """
        Build API response in the exact same format as AuctionPipeline.
        """
        from app.core.schemas.auction_schemas import build_pipeline_response
        return build_pipeline_response(result)
