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

            # 2. Render PDF pages as images
            logger.info("Rendering PDF pages to images.")
            doc = fitz.open(pdf_path)
            page_images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                page_images.append(img)
            doc.close()

            logger.info(f"Total pages rendered: {len(page_images)}")

            # 3. Chunk pages into groups of 4 and stitch them
            stitched_images_paths = []
            upload_dir = os.path.dirname(pdf_path)
            
            for i in range(0, len(page_images), 4):
                chunk = page_images[i:i+4]
                stitched_img = self.stitch_pages(chunk)
                
                # Save stitched image physically
                stitched_filename = f"{upload.upload_number}_stitched_{i//4}.png"
                stitched_path = os.path.join(upload_dir, stitched_filename)
                stitched_img.save(stitched_path, "PNG")
                stitched_images_paths.append(stitched_path)

            logger.info(f"Generated {len(stitched_images_paths)} stitched grid images.")

            # 4. Process each stitched image via Vision LLM
            saved_records = []
            extraction_results = []
            total_notices = 0

            for idx, img_path in enumerate(stitched_images_paths):
                logger.info(f"Processing stitched grid {idx + 1}/{len(stitched_images_paths)}")
                
                # Base64 encode the stitched image
                with open(img_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode("utf-8")

                ocr_text = ""
                try:
                    logger.info(f"Running OCR on stitched image {img_path}")
                    ocr_text = self.ocr.extract_text(img_path)
                except Exception:
                    logger.exception("OCR failed on stitched image, proceeding without it.")

                try:
                    parsed = self.parser.process_vision(
                        base64_image,
                        ocr_text=ocr_text,
                        global_ocr_text=""
                    )
                    
                    success = True
                    records = parsed.get("record", {})
                    
                    # Convert to list if it is a single dict
                    if isinstance(records, dict):
                        records = [records]
                    elif not isinstance(records, list):
                        records = []

                    # Save each record to database
                    for record in records:
                        record["upload_id"] = upload.id
                        saved = await self.database.save_auction(record)
                        saved_records.append(saved)
                        total_notices += 1

                    extraction_results.append({
                        "success": True,
                        "image": img_path,
                        "message": "Processed successfully."
                    })
                except Exception as exc:
                    logger.exception(f"Failed to process stitched image {img_path}")
                    extraction_results.append({
                        "success": False,
                        "image": img_path,
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
        records_dict = []
        
        for record in result["results"]:
            if hasattr(record, "__table__"):
                record_dict = {c.key: getattr(record, c.key) for c in record.__table__.columns}
                for k, v in record_dict.items():
                    if isinstance(v, Decimal):
                        record_dict[k] = float(v)
                    elif isinstance(v, (datetime, date)):
                        record_dict[k] = v.isoformat()
                
                # Expose aliases for HTML frontend compatibility
                record_dict["reserve_price"] = record_dict.get("auction_start_price")
                record_dict["auction_id"] = record_dict.get("notice_auction_id")
                records_dict.append(record_dict)
            else:
                records_dict.append(record)

        error_msg = None
        if len(records_dict) == 0 and "extraction_results" in result:
            for res in result["extraction_results"]:
                if not res.get("success") and res.get("message"):
                    error_msg = res["message"]
                    break

        response = {
            "success": len(records_dict) > 0 or result["summary"]["total_notices"] == 0,
            "upload_id": result["upload"].id,
            "upload_number": result["upload"].upload_number,
            "total_records": len(records_dict),
            "records": records_dict,
            "summary": result["summary"],
        }

        if error_msg:
            response["message"] = error_msg

        return response
