"""
Document Processing Pipeline for PDF Auction processing.
Delegates 100% execution to PDFParserService (Version 2.0 Stages 1-16 Candidate Extraction Engine).
"""

from __future__ import annotations

import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.repositories.upload_repository import UploadRepository
from app.services.upload.upload_service import UploadService
from app.services.pdf.pdf_parser_service import PDFParserService
from app.services.storage.database_service import DatabaseService
from app.core.schemas.auction_schemas import build_pipeline_response

logger = get_logger(__name__)

class DocumentPipeline:
    """
    Document processing pipeline delegating directly to PDFParserService (Stages 1 - 16).
    """

    def __init__(self, db: AsyncSession) -> None:
        logger.info("Initializing Document Processing Pipeline (PDFParserService Delegator).")
        self.db = db
        repository = UploadRepository(db)
        self.upload_service = UploadService(repository=repository)
        self.pdf_service = PDFParserService()
        self.database = DatabaseService(db)

    async def run(self, file) -> dict:
        """
        Execute PDF document extraction using Stages 1-16 PDF Processing Pipeline.
        """
        logger.info("Starting Document Pipeline execution delegating to PDFParserService.")

        try:
            # 1. Upload and store PDF file
            upload = await self.upload_service.upload_file(file)
            pdf_path = upload.original_file_path

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Uploaded PDF not found at {pdf_path}")

            # 2. Route directly to PDFParserService (Stages 1 - 16)
            logger.info("Routing PDF directly to PDFParserService: %s", pdf_path)
            pdf_result = self.pdf_service.process_pdf_file(pdf_path)
            records = pdf_result.get("records", [])

            # 3. Save extracted lot records into database
            saved_records = []
            for rec in records:
                try:
                    rec["upload_id"] = upload.id
                    saved = await self.database.save_auction(rec)
                    saved_records.append(saved)
                except Exception as exc:
                    logger.exception("Unable to save PDF auction record: %s", exc)

            total_notices = len(saved_records)

            # Update upload status
            await self.upload_service.repository.update_status(upload=upload, status="COMPLETED")
            await self.upload_service.repository.update_statistics(
                upload=upload,
                total_notices=total_notices,
                successful_notices=total_notices,
                failed_notices=0 if total_notices > 0 else 1,
                processing_time=pdf_result.get("processing_time", 0.0),
                confidence_score=0.99
            )

            result = {
                "upload": upload,
                "results": saved_records,
                "summary": {
                    "total_notices": total_notices,
                    "successful": total_notices,
                    "failed": 0 if total_notices > 0 else 1
                },
                "extraction_results": [{
                    "success": True,
                    "document": pdf_path,
                    "message": f"Processed PDF via Stages 1-16 Engine ({total_notices} output records generated)."
                }]
            }

            return build_pipeline_response(result)

        except Exception as exc:
            logger.exception("Document pipeline execution failed: %s", str(exc))
            return {
                "success": False,
                "message": str(exc)
            }
