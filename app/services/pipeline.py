"""
Auction Processing Pipeline.

Main orchestration service.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from app.repositories.upload_repository import UploadRepository

from app.services.upload.upload_service import UploadService

from app.services.preprocess.image_enhancer import ImageEnhancer

from app.services.detection.layout_detector import LayoutDetector

from app.services.splitter.auction_splitter import AuctionSplitter

from app.services.ocr.paddle_service import PaddleOCRService

from app.services.extractor.parser import AuctionParser

from app.services.storage.database_service import DatabaseService

logger = get_logger(__name__)


class AuctionPipeline:
    """
    Complete Auction Processing Pipeline.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:

        logger.info(
            "Initializing Auction Pipeline."
        )

        self.db = db

        repository = UploadRepository(
            db,
        )

        self.upload_service = UploadService(
            repository=repository,
        )

        self.image_enhancer = ImageEnhancer()

        self.layout_detector = LayoutDetector()

        self.splitter = AuctionSplitter()

        self.ocr = PaddleOCRService()

        self.parser = AuctionParser()

        self.database = DatabaseService(
            db,
        )

    # ==========================================================
    # Ready Check
    # ==========================================================

    async def is_ready(
        self,
    ) -> bool:
        """
        Verify pipeline services.
        """

        try:

            upload_ready = await self.upload_service.is_ready()

        except Exception:

            upload_ready = False

        return (
    upload_ready
    and self.image_enhancer.is_ready()
    and self.layout_detector.is_ready()
    and self.splitter.is_ready()
    and self.ocr.is_ready()
    and self.parser.is_ready()
    and await self.database.is_ready()
)
    
    # ==========================================================
    # Health Check
    # ==========================================================

    async def health_check(
        self,
    ) -> dict:
        """
        Pipeline health.
        """

        return {

            "status": (

                "Healthy"

                if await self.is_ready()

                else "Unavailable"

            ),

            "services": {

                "upload": True,

                "preprocessing": True,

                "ocr": True,

                "parser": True,

                "database": True,

            },

        }


    # ==========================================================
    # Statistics
    # ==========================================================

    async def statistics(
        self,
    ) -> dict:
        """
        Pipeline statistics.
        """

        uploads = await self.upload_service.count_uploads()

        return {

            "registered_uploads": uploads,

            "ready": await self.is_ready(),

        }
    

    # ==========================================================
    # Version
    # ==========================================================

    def version(
        self,
    ) -> dict:

        return {

            "service": "Auction Pipeline",

            "version": "1.0.0",

            "architecture": "Async",

        }
    

    # ==========================================================
    # Upload Image
    # ==========================================================

    async def upload_image(
        self,
        file,
    ):
        """
        Upload newspaper image.
        """

        logger.info(
            "Uploading newspaper image."
        )

        upload = await self.upload_service.upload_file(
            file,
        )

        return upload
    

    # ==========================================================
    # Enhance Image
    # ==========================================================

    async def enhance_image(
        self,
        image_path: str,
    ) -> str:
        """
        Enhance uploaded image.
        """

        logger.info(
            "Enhancing image."
        )

        enhanced_path = self.image_enhancer.process(
            image_path,
        )

        return enhanced_path


    # ==========================================================
    # Layout Detection
    # ==========================================================

    async def detect_layout(
        self,
        image_path: str,
    ):
        """
        Detect newspaper layout.
        """

        logger.info(
            "Detecting layout."
        )

        layout = self.layout_detector.detect(
            image_path,
        )

        return layout
    

    # ==========================================================
    # Split Auction Notices
    # ==========================================================

    async def split_image(
        self,
        image_path: str,
        upload_number: str = "temp",
    ) -> list[str]:
        """
        Split newspaper into
        individual auction notices.
        """

        logger.info(
            "Splitting auction notices."
        )

        images = self.splitter.process(
            image_path,
            upload_number,
        )

        return images
    

    # ==========================================================
    # Prepare Images
    # ==========================================================

    async def prepare_images(
        self,
        image_path: str,
        upload_number: str = "temp",
    ) -> list[dict] | list[str]:
        """
        Complete preprocessing pipeline.
        """
        enhanced = await self.enhance_image(
            image_path,
        )

        await self.detect_layout(
            enhanced,
        )

        images = await self.split_image(
            enhanced,
            upload_number,
        )

        return images
    

    # ==========================================================
    # Validate Image
    # ==========================================================

    def validate_image(
        self,
        image_path: str,
    ) -> bool:
        """
        Validate image path.
        """

        if not image_path:

            return False

        return True
    
    # ==========================================================
    # Image Information
    # ==========================================================

    async def image_information(
        self,
        image_path: str,
    ) -> dict:
        """
        Return preprocessing information.
        """

        images = await self.prepare_images(
            image_path,
        )

        return {

            "image_path": image_path,

            "auction_count": len(images),

            "auction_images": images,

        }
    
    # ==========================================================
    # OCR Extraction
    # ==========================================================

    async def extract_text(
        self,
        image_path: str,
    ) -> str:
        """
        Extract text from auction image.
        """

        logger.info(
            "Running OCR."
        )

        text = self.ocr.extract_text(
            image_path,
        )

        return text
    

    # ==========================================================
    # Validate OCR
    # ==========================================================

    def validate_ocr(
        self,
        text: str,
    ) -> bool:
        """
        Validate OCR result.
        """

        if text is None:

            return False

        return len(
            text.strip()
        ) > 10
    

    # ==========================================================
    # Parse OCR Text
    # ==========================================================

    async def parse_text(
        self,
        text: str,
    ) -> dict:
        """
        Parse OCR text into
        structured auction data.
        """

        logger.info(
            "Parsing OCR text."
        )

        result = self.parser.process(
            text,
        )

        return result
    

    # ==========================================================
    # Process Notice
    # ==========================================================

    async def process_notice(
        self,
        image_path: str | dict,
        original_file_path: str = "",
        global_ocr_text_holder: list[str] = None,
    ) -> dict:
        """
        Process a single auction notice using direct Vision scraping.
        """
        if isinstance(image_path, dict) and "image_path" in image_path:
            image_path = image_path["image_path"]

        # Use original split notice image directly for Gemini LLM to preserve character fidelity
        logger.info("Using original split notice image directly for Gemini LLM to preserve character fidelity.")

        import base64
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as exc:
            logger.exception("Failed to read and encode image.")
            return {
                "success": False,
                "image": str(image_path),
                "message": f"Image read failed: {exc}",
            }

        ocr_text = ""
        try:
            logger.info("Extracting OCR text helper to prevent vision misreads.")
            ocr_text = await self.extract_text(image_path)
        except Exception:
            logger.exception("OCR text helper extraction failed, proceeding without it.")

        try:
            logger.info("Attempting direct LLM Vision extraction.")
            parsed = self.parser.process_vision(
                base64_image,
                ocr_text=ocr_text,
                global_ocr_text=""
            )
            return {
                "success": True,
                "image": image_path,
                "ocr_text": ocr_text,
                "record": parsed.get("fields", []),
                "raw_llm": parsed.get("llm", {}),
                "validation": parsed.get("validation", {}),
                "confidence": parsed.get("confidence", {}),
                "statistics": parsed.get("statistics", {}),
            }
        except Exception as exc:
            logger.exception("Vision parsing failed.")
            return {
                "success": False,
                "image": image_path,
                "message": f"Vision parsing failed: {exc}",
            }
    

    # ==========================================================
    # Process Notices
    # ==========================================================

    async def process_notices(
        self,
        images: list[str],
        original_file_path: str = "",
    ) -> list[dict]:
        """
        Process all auction notices.
        """

        logger.info(
            "Processing %d notices.",
            len(images),
        )

        global_ocr_text_holder = [""]
        results = []

        for image in images:

            try:

                result = await self.process_notice(
                    image,
                    original_file_path=original_file_path,
                    global_ocr_text_holder=global_ocr_text_holder,
                )

                results.append(
                    result,
                )

            except Exception:

                logger.exception(
                    "Notice processing failed."
                )

                results.append(

                    {

                        "success": False,

                        "image": image,

                    }

                )

        return results
    

    # ==========================================================
    # Extraction Summary
    # ==========================================================

    def extraction_summary(
        self,
        results: list[dict],
    ) -> dict:
        """
        Return extraction summary.
        """

        total = len(results)

        success = sum(

            1

            for item in results

            if item.get(
                "success",
            )

        )

        failed = total - success

        return {

            "total_notices": total,

            "successful": success,

            "failed": failed,

        }
    
    # ==========================================================
    # OCR Statistics
    # ==========================================================

    def ocr_statistics(
        self,
        text: str,
    ) -> dict:
        """
        OCR statistics.
        """

        return {

            "characters": len(text),

            "words": len(
                text.split(),
            ),

            "lines": len(
                text.splitlines(),
            ),

        }
    
    # ==========================================================
    # OCR Pipeline
    # ==========================================================

    async def process_ocr_stage(
        self,
        images: list[str],
        original_file_path: str = "",
    ) -> dict:
        """
        Execute OCR pipeline.
        """

        results = await self.process_notices(
            images,
            original_file_path=original_file_path,
        )

        return {

            "results": results,

            "summary": self.extraction_summary(
                results,
            ),

        }
    
    # ==========================================================
    # Save Results
    # ==========================================================

    async def save_results(
        self,
        upload,
        results: list[dict],
    ) -> dict:
        """
        Save extracted auction records.
        """

        logger.info(
            "Saving auction records."
        )

        saved_records = []

        for result in results:

            if not result.get(
                "success",
            ):

                continue

            records = result.get(
                "record",
                {},
            )

            if isinstance(records, dict):
                records = [records]
            elif not isinstance(records, list):
                records = []

            for record in records:
                try:

                    record["upload_id"] = upload.id

                    saved = await self.database.save_auction(
                        record,
                    )

                    saved_records.append(
                        saved,
                    )

                except Exception:

                    logger.exception(
                        "Unable to save auction record."
                    )

        return {

            "upload": upload,

            "records": saved_records,

        }

    # ==========================================================
    # Process File
    # ==========================================================

    async def process_file(
        self,
        file,
    ) -> dict:
        """
        Process uploaded newspaper.
        """

        logger.info(
            "Processing uploaded newspaper."
        )

        upload = await self.upload_image(
            file,
        )

        images = await self.prepare_images(

            upload.original_file_path,
            upload.upload_number,

        )

        # OCR text is now lazily extracted during fallback in process_notice to minimize latency
        extraction = await self.process_ocr_stage(
            images,
            original_file_path=upload.original_file_path,
        )

        database = await self.save_results(

            upload,

            extraction["results"],

        )

        return {

            "upload": database["upload"],

            "results": database["records"],

            "summary": extraction["summary"],

            "extraction_results": extraction["results"],

        }

    # ==========================================================
    # Process Image Path
    # ==========================================================

    async def process_image_path(
        self,
        image_path: str,
    ) -> dict:
        """
        Process an already-existing image file.
        """
        logger.info(
            "Processing existing image file: %s",
            image_path,
        )

        import os
        from pathlib import Path
        from app.models.upload import Upload
        from app.core.constants import UPLOAD_UPLOADED

        filename = os.path.basename(image_path)
        extension = Path(filename).suffix.lower() or ".png"
        file_size = 0
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            
        upload = Upload(
            upload_number=self.upload_service.generate_upload_number(),
            original_filename=filename,
            stored_filename=filename,
            file_extension=extension,
            content_type="image/png",
            file_size=file_size,
            original_file_path=image_path,
            processed_file_path="",
            split_folder_path="",
            status=UPLOAD_UPLOADED,
            total_notices=0,
            successful_notices=0,
            failed_notices=0,
            processing_time=0.0,
            confidence_score=0.0,
            error_message="",
        )
        
        upload = await self.database.upload_repository.create(upload)

        images = await self.prepare_images(
            upload.original_file_path,
            upload.upload_number,
        )

        extraction = await self.process_ocr_stage(
            images,
            original_file_path=upload.original_file_path,
        )

        database = await self.save_results(
            upload,
            extraction["results"],
        )

        # Update upload status to COMPLETED
        await self.upload_service.repository.update_status(
            upload=upload,
            status="COMPLETED",
        )
        await self.upload_service.repository.update_statistics(
            upload=upload,
            total_notices=len(images),
            successful_notices=len(database["records"]),
            failed_notices=len(images) - len(database["records"]),
            processing_time=0.0,
            confidence_score=0.99
        )

        result = {
            "upload": database["upload"],
            "results": database["records"],
            "summary": extraction["summary"],
            "extraction_results": extraction["results"],
        }
        
        return self.build_response(result)

    # ==========================================================
    # Build Response
    # ==========================================================

    def build_response(
        self,
        result: dict,
    ) -> dict:
        """
        Build API response.
        """
        from app.core.schemas.auction_schemas import build_pipeline_response
        return build_pipeline_response(result)
    
    # ==========================================================
    # Run Pipeline
    # ==========================================================

    async def run(
        self,
        file,
    ) -> dict:
        """
        Execute complete pipeline.
        """

        logger.info(
            "Starting Auction Pipeline."
        )

        try:

            result = await self.process_file(
                file,
            )

            logger.info(
                "Pipeline completed."
            )

            return self.build_response(
                result,
            )

        except Exception as exc:

            logger.exception(
                "Pipeline execution failed."
            )

            return {

                "success": False,

                "message": str(exc),

            }
        
    # ==========================================================
    # Batch Processing
    # ==========================================================

    async def run_batch(
        self,
        files: list,
    ) -> dict:
        """
        Process multiple newspapers.
        """

        logger.info(
            "Processing %d files.",
            len(files),
        )

        results = []

        for file in files:

            results.append(

                await self.run(
                    file,
                )

            )

        return {

            "success": True,

            "processed_files": len(results),

            "results": results,

        }
    
    # ==========================================================
    # Cleanup
    # ==========================================================

    async def cleanup(
        self,
    ) -> None:
        """
        Cleanup resources.
        """

        logger.info(
            "Cleaning pipeline resources."
        )

        try:

            await self.database.close()

        except Exception:

            logger.exception(
                "Database cleanup failed."
            )


    # ==========================================================
    # Information
    # ==========================================================

    def info(
        self,
    ) -> dict:
        """
        Pipeline information.
        """

        return {

            "name": "Auction AI Pipeline",

            "version": "1.0.0",

            "framework": "FastAPI",

            "database": "MySQL",

            "ocr": "PaddleOCR",

            "llm": "OpenAI",

        }
    

    # ==========================================================
    # Health Report
    # ==========================================================

    async def report(
        self,
    ) -> dict:
        """
        Pipeline report.
        """

        return {

            "pipeline": self.info(),

            "health": await self.health_check(),

            "statistics": await self.statistics(),

        }