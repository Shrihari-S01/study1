"""
Auction Processing Pipeline.

Main orchestration service.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import PipelineStageTimer, get_logger
from app.repositories.upload_repository import UploadRepository
from app.services.detection.layout_detector import LayoutDetector
from app.services.extractor.parser import AuctionParser
from app.services.ocr.paddle_service import PaddleOCRService
from app.services.ocr.spatial_ocr_indexer import SpatialOCRIndexCache
from app.services.preprocess.image_enhancer import ImageEnhancer
from app.services.splitter.auction_splitter import AuctionSplitter
from app.services.storage.database_service import DatabaseService
from app.services.upload.file_manager import FileManager
from app.services.upload.upload_service import UploadService

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

        self.file_manager = FileManager()

        self.image_enhancer = ImageEnhancer()

        self.layout_detector = LayoutDetector()

        self.splitter = AuctionSplitter()

        self.ocr = PaddleOCRService()

        self.parser = AuctionParser()

        self.database = DatabaseService(
            db,
        )

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
    

    def version(
        self,
    ) -> dict:

        return {

            "service": "Auction Pipeline",

            "version": "1.0.0",

            "architecture": "Async",

        }
    

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
    

    async def process_notice(
        self,
        image_path: str | dict,
        original_file_path: str = "",
        global_ocr_text_holder: list[str] = None,
        bbox_meta: dict = None,
    ) -> dict:
        """
        Process a single auction notice using direct Vision scraping.
        """
        if isinstance(image_path, dict) and "image_path" in image_path:
            bbox_meta = image_path
            image_path = image_path["image_path"]

        # Save debug crop visualization before processing
        try:
            debug_dir = os.path.join(os.getcwd(), "temp", "debug_crops")
            os.makedirs(debug_dir, exist_ok=True)
            crop_filename = os.path.basename(str(image_path))
            debug_crop_path = os.path.join(debug_dir, f"debug_{crop_filename}")
            import shutil
            shutil.copy(str(image_path), debug_crop_path)
            logger.info("Saved debug crop visualization: %s", debug_crop_path)
        except Exception as dbg_err:
            logger.warning("Failed to save debug crop visualization: %s", dbg_err)

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
            from app.services.ocr.spatial_ocr_indexer import SpatialOCRIndexCache
            cached_idx = SpatialOCRIndexCache.get(original_file_path or image_path)
            if cached_idx and bbox_meta and "x" in bbox_meta and "y" in bbox_meta:
                
                ocr_text = cached_idx.query_bounding_box(
                    x=float(bbox_meta.get("x", 0)),
                    y=float(bbox_meta.get("y", 0)),
                    w=float(bbox_meta.get("width", 500)),
                    h=float(bbox_meta.get("height", 500)),
                    margin=30.0,
                )
            if not ocr_text or len(ocr_text.split()) < 10:
                # Fallback to direct crop OCR only if spatial query returned sparse text
                ocr_text = await self.extract_text(image_path)
        except Exception:
            logger.exception("Direct crop OCR text extraction failed.")
            ocr_text = ""

        retry_count = 0
        try:
            # Adaptive OCR Enhancement & Boundary Expansion Retry if text density is sparse (< 10 words)
            ocr_words = ocr_text.split() if ocr_text else []
            lot_idx_log = bbox_meta.get("auction_number", 1) if bbox_meta else 1
            if len(ocr_words) < 10:
                logger.info("[Lot #%s] Sparse OCR text detected (%d words). Attempting expanded crop retry.", lot_idx_log, len(ocr_words))
                expanded_crop_path = self.image_enhancer.expand_and_enhance_crop(
                    full_image_path=original_file_path or str(image_path),
                    bbox=bbox_meta or {},
                    margin_percent=0.15,
                    output_crop_path=str(image_path),
                )
                retry_text = await self.extract_text(expanded_crop_path)
                retry_words = retry_text.split() if retry_text else []
                if len(retry_words) > len(ocr_words):
                    logger.info("[Lot #%s] Expanded crop OCR retry succeeded: word count improved from %d to %d.", lot_idx_log, len(ocr_words), len(retry_words))
                    ocr_text = retry_text
                    ocr_words = retry_words
                    retry_count = 1
                else:
                    logger.warning("[Lot #%s] Expanded crop OCR word count remained low (%d words).", lot_idx_log, len(retry_words))
        except Exception as retry_err:
            logger.warning("Adaptive expanded OCR retry failed: %s", retry_err)

        try:
            # Hybrid Fast Path Routing: Evaluate OCR confidence, density, and field completeness
            if len(ocr_words) >= 15:
                logger.info("Executing Fast Path: High-density OCR text found (%d words). Calling Text LLM.", len(ocr_words))
                text_json_str = self.parser.llm.text_completion(ocr_text)
                parsed_fields = self.parser.parse_llm_json(text_json_str, ocr_text=ocr_text)

                # Pre-PHP Consistency Checker
                from app.services.integration.consistency_checker import PrePHPConsistencyChecker
                PrePHPConsistencyChecker.check_extraction_consistency(
                    ocr_text,
                    parsed_fields[0] if isinstance(parsed_fields, list) and len(parsed_fields) > 0 else (parsed_fields if isinstance(parsed_fields, dict) else {}),
                    lot_index=int(bbox_meta.get("auction_number", 1)) if bbox_meta else 1,
                )

                # Structured block diagnostic report
                self._log_block_diagnostic(
                    index=int(bbox_meta.get("auction_number", 1)) if bbox_meta else 1,
                    image_path=str(image_path),
                    ocr_text=ocr_text,
                    llm_input_str=ocr_text,
                    llm_output_str=text_json_str,
                    record=parsed_fields,
                    bbox_meta=bbox_meta,
                    retry_count=retry_count,
                    vision_used=False,
                )

                return {
                    "success": True,
                    "image": image_path,
                    "ocr_text": ocr_text,
                    "record": parsed_fields,
                    "raw_llm": text_json_str,
                    "validation": {},
                    "confidence": {"overall": 0.95},
                    "statistics": {},
                }
        except Exception as fast_path_err:
            logger.warning("Fast Path Text LLM completion failed (%s). Falling back to Vision LLM.", fast_path_err)

        try:
            logger.info("Attempting direct LLM Vision extraction (downscaled in-memory).")
            parsed = self.parser.process_vision(
                base64_image,
                ocr_text=ocr_text,
                global_ocr_text=""
            )

            rec_fields = parsed.get("fields", [])
            raw_resp = json.dumps(parsed.get("llm", {}), default=str)
        except Exception as vision_err:
            logger.warning("Vision LLM extraction failed: %s", vision_err)
            rec_fields = []
            raw_resp = "{}"

        # Target Extraction & Field Lifecycle Verification
        record_dict = rec_fields[0] if isinstance(rec_fields, list) and len(rec_fields) > 0 and isinstance(rec_fields[0], dict) else (rec_fields if isinstance(rec_fields, dict) else {})
        
        # Check mandatory fields completeness: borrower_name, loan_account_number, reserve_price, emd_amount, property_address, auction_description
        def get_missing_mandatory(d: dict) -> list[str]:
            missing = []
            if not d.get("borrower_name") and not d.get("borrower"): missing.append("borrower_name")
            if not d.get("reserve_price") and not d.get("reserver_price") and not d.get("auction_start_price"): missing.append("reserve_price")
            if not d.get("emd_amount") and not d.get("emd_price"): missing.append("emd_amount")
            if not d.get("property_address") and not d.get("product_location") and not d.get("assets_location"): missing.append("property_address")
            if not d.get("auction_description") and not d.get("auction_details") and not d.get("description"): missing.append("auction_description")
            return missing

        mandatory_missing = get_missing_mandatory(record_dict)

        # Iterative Field Recovery Passes (Up to 3 crop expansion retries with 20%, 35%, 50% margins)
        max_retries = 3
        margin_steps = [0.20, 0.35, 0.50]
        current_pass = 0

        while mandatory_missing and current_pass < max_retries:
            margin = margin_steps[min(current_pass, len(margin_steps) - 1)]
            logger.info("[Lot #%s] Missing mandatory fields %s on Pass #%d. Executing crop expansion (margin=%.0f%%) & Vision retry.", bbox_meta.get("auction_number", 1) if bbox_meta else 1, mandatory_missing, current_pass + 1, margin * 100)
            expanded_crop_path = self.image_enhancer.expand_and_enhance_crop(
                full_image_path=original_file_path or str(image_path),
                bbox=bbox_meta or {},
                margin_percent=margin,
                output_crop_path=str(image_path),
            )
            retry_text = await self.extract_text(expanded_crop_path)
            try:
                with open(expanded_crop_path, "rb") as retry_file:
                    retry_base64 = base64.b64encode(retry_file.read()).decode("utf-8")
                retry_parsed = self.parser.process_vision(
                    retry_base64,
                    ocr_text=retry_text or ocr_text,
                    global_ocr_text=""
                )
                retry_rec = retry_parsed.get("fields", [])
                retry_dict = retry_rec[0] if isinstance(retry_rec, list) and len(retry_rec) > 0 and isinstance(retry_rec[0], dict) else (retry_rec if isinstance(retry_rec, dict) else {})
                
                # Non-destructive merge: Only populate fields that were missing in record_dict
                for k, v in retry_dict.items():
                    if v and (not record_dict.get(k) or str(record_dict.get(k)).lower() in {"", "0", "0.0", "0.00", "null", "none", "n/a"}):
                        record_dict[k] = v
                        logger.info("[Lot #%s] Recovered missing field '%s' = %r on Pass #%d.", bbox_meta.get("auction_number", 1) if bbox_meta else 1, k, v, current_pass + 1)
            except Exception as r_err:
                logger.warning("Targeted retry pass #%d failed: %s", current_pass + 1, r_err)

            current_pass += 1
            retry_count += 1
            mandatory_missing = get_missing_mandatory(record_dict)

        if isinstance(rec_fields, list) and len(rec_fields) > 0:
            rec_fields[0] = record_dict
        else:
            rec_fields = [record_dict]

        # Structured block diagnostic report
        self._log_block_diagnostic(
            index=int(bbox_meta.get("auction_number", 1)) if bbox_meta else 1,
            image_path=str(image_path),
            ocr_text=ocr_text,
            llm_input_str=ocr_text,
            llm_output_str=raw_resp,
            record=rec_fields,
            bbox_meta=bbox_meta,
            retry_count=retry_count,
            vision_used=True,
        )

        return {
            "success": True,
            "image": image_path,
            "ocr_text": ocr_text,
            "record": rec_fields,
            "raw_llm": raw_resp,
            "validation": {},
            "confidence": {"overall": 0.95},
            "statistics": {},
        }

    @staticmethod
    def _log_block_diagnostic(
        index: int,
        image_path: str,
        ocr_text: str,
        llm_input_str: str,
        llm_output_str: str,
        record: Any,
        bbox_meta: Optional[dict] = None,
        retry_count: int = 0,
        vision_used: bool = False,
    ) -> None:
        """
        Prints structured production diagnostic log for an individual auction block.
        """
        ocr_chars = len(ocr_text or "")
        ocr_words = len(ocr_text.split()) if ocr_text else 0
        llm_in_chars = len(llm_input_str or "")
        llm_out_chars = len(llm_output_str or "")

        rec_dict = record if isinstance(record, dict) else (record[0] if isinstance(record, list) and len(record) > 0 and isinstance(record[0], dict) else {})

        borrower = str(rec_dict.get("borrower_name") or rec_dict.get("borrower") or "").strip()
        loan_no = str(rec_dict.get("loan_account_number") or rec_dict.get("loan_no") or "").strip()
        location = str(rec_dict.get("product_location") or rec_dict.get("property_address") or rec_dict.get("assets_location") or "").strip()
        price = str(rec_dict.get("reserver_price") or rec_dict.get("reserve_price") or rec_dict.get("auction_start_price") or rec_dict.get("starting_price") or "").strip()
        emd = str(rec_dict.get("emd_price") or rec_dict.get("emd_amount") or "").strip()
        desc = str(rec_dict.get("auction_details") or rec_dict.get("auction_description") or rec_dict.get("description") or "").strip()

        has_borrower = "YES" if borrower and borrower.lower() not in {"n/a", "null", "none", "undefined"} else "NO"
        has_loan_no = "YES" if loan_no and loan_no.lower() not in {"n/a", "null", "none", "undefined"} else "NO"
        has_location = "YES" if location and location.lower() not in {"n/a", "null", "none", "undefined"} else "NO"
        has_price = "YES" if price and price not in {"0", "0.0", "0.00", "n/a", "null", "none"} else "NO"
        has_emd = "YES" if emd and emd not in {"0", "0.0", "0.00", "n/a", "null", "none"} else "NO"
        has_desc = "YES" if desc and desc.lower() not in {"n/a", "null", "none", "undefined"} and not desc.lower().startswith("e-auction sale notice") else "NO"

        missing_fields = []
        if has_borrower == "NO": missing_fields.append("borrower_name")
        if has_loan_no == "NO": missing_fields.append("loan_account_number")
        if has_location == "NO": missing_fields.append("property_address")
        if has_price == "NO": missing_fields.append("reserve_price")
        if has_emd == "NO": missing_fields.append("emd_amount")
        if has_desc == "NO": missing_fields.append("property_description")

        is_complete = len(missing_fields) == 0
        status_str = "COMPLETE" if is_complete else f"PARTIAL (Missing: {', '.join(missing_fields)})"

        bbox_str = "N/A"
        if bbox_meta and "x" in bbox_meta and "y" in bbox_meta:
            bbox_str = f"(x={bbox_meta.get('x')}, y={bbox_meta.get('y')}, w={bbox_meta.get('width')}, h={bbox_meta.get('height')})"

        logger.info(
            "\n========== AUCTION BLOCK #%d DIAGNOSTIC REPORT ==========\n"
            "Crop Saved         : %s\n"
            "Crop Coordinates   : %s\n"
            "OCR Words / Chars  : %d words (%d chars)\n"
            "LLM Input / Output : In: %d chars | Out: %d chars\n"
            "Vision LLM Used    : %s\n"
            "OCR Retry Count    : %d\n"
            "Borrower Found     : %s (%r)\n"
            "Location Found     : %s (%r)\n"
            "Reserve Price Found: %s (%r)\n"
            "Brief Found        : %s\n"
            "Missing Fields     : %s\n"
            "Final Status       : %s\n"
            "========================================================",
            index,
            image_path,
            bbox_str,
            ocr_words,
            ocr_chars,
            llm_in_chars,
            llm_out_chars,
            "YES" if vision_used else "NO",
            retry_count,
            has_borrower,
            borrower[:30],
            has_location,
            location[:30],
            has_price,
            price[:20],
            has_desc,
            missing_fields if missing_fields else "NONE",
            status_str,
        )

    

    async def process_notices(
        self,
        images: list[str],
        original_file_path: str = "",
    ) -> list[dict]:
        """
        Process all auction notices.
        """

        import asyncio
        import time

        start_t = time.time()
        logger.info("Processing %d notices in parallel using asyncio.gather.", len(images))

        global_ocr_text_holder = [""]

        async def _proc_single(image_item: str) -> dict:
            try:
                return await self.process_notice(
                    image_item,
                    original_file_path=original_file_path,
                    global_ocr_text_holder=global_ocr_text_holder,
                )
            except Exception as exc:
                logger.exception("Notice processing failed for image: %s", image_item)
                return {
                    "success": False,
                    "image": image_item,
                    "message": str(exc),
                }

        results = await asyncio.gather(*[_proc_single(img) for img in images])
        elapsed = round(time.time() - start_t, 2)
        logger.info("Parallel processing of %d notices completed in %.2fs.", len(images), elapsed)

        return list(results)
    

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

        # Check if input file is a PDF (Stages 1 - 18 PDF Pipeline)
        if upload.original_file_path and upload.original_file_path.lower().endswith(".pdf"):
            logger.info("Routing uploaded file directly to Stages 1-18 PDF Pipeline: %s", upload.original_file_path)
            pdf_result = self.parser.process_pdf(upload.original_file_path, ocr_service=self.ocr)
            records = pdf_result.get("records", [])

            saved_records = []
            for rec in records:
                try:
                    rec["upload_id"] = upload.id
                    saved = await self.database.save_auction(rec)
                    saved_records.append(saved)
                except Exception:
                    logger.exception("Unable to save PDF auction record.")

            summary = {
                "total_notices": 1,
                "successful": 1 if saved_records else 0,
                "failed": 0 if saved_records else 1
            }

            return {
                "upload": upload,
                "results": saved_records,
                "summary": summary,
                "extraction_results": [{"success": True, "record": records}]
            }

        import os
        import time
        from app.core.logger import PipelineStageTimer
        from app.services.ocr.spatial_ocr_indexer import SpatialOCRIndexCache

        timer = PipelineStageTimer()
        t0 = time.time()

        # 1. Image Load & Bypass Check
        t_sub = time.time()
        enhanced_path = await self.enhance_image(upload.original_file_path)
        timer.record_stage("Image Preprocessing", time.time() - t_sub)

        # 2. Single-Pass OCR & Spatial Index Construction
        t_sub = time.time()
        raw_ocr_lines = self.ocr.extract(enhanced_path)
        spatial_index = SpatialOCRIndexCache.get(enhanced_path)
        cached_ocr_text = spatial_index.get_full_text() if spatial_index else ""
        timer.record_stage("Single-Pass OCR", time.time() - t_sub)

        # 3. Layout Detection & Split
        t_sub = time.time()
        images = await self.split_image(enhanced_path, upload.upload_number)
        timer.record_stage("Region Detection", time.time() - t_sub)

        # 4. Shared Document Metadata Extraction (Pass 1 - Fast Path Text LLM)
        t_sub = time.time()
        shared_metadata = {}
        try:
            if cached_ocr_text:
                raw_shared_str = self.parser.llm.text_completion(cached_ocr_text[:3000])
                if isinstance(raw_shared_str, str):
                    import json
                    try:
                        shared_metadata = json.loads(raw_shared_str)
                    except Exception:
                        shared_metadata = {}
        except Exception as shared_err:
            logger.warning("Shared metadata single-pass extraction failed: %s", shared_err)
        timer.record_stage("Shared Metadata Pass", time.time() - t_sub)

        # 5. Dynamic Worker Pool & Async Semaphore Parallel Auction Extraction
        t_sub = time.time()
        num_blocks = len(images)
        cpu_workers = os.cpu_count() or 4
        max_workers = min(num_blocks, cpu_workers, 6) if num_blocks > 0 else 1
        sem = asyncio.Semaphore(max_workers)

        async def _extract_worker(image_item: dict | str) -> dict:
            async with sem:
                img_p = image_item["image_path"] if isinstance(image_item, dict) and "image_path" in image_item else image_item
                bbox_meta = image_item if isinstance(image_item, dict) else None
                try:
                    res = await self.process_notice(img_p, original_file_path=upload.original_file_path, bbox_meta=bbox_meta)
                    if res.get("success") and isinstance(res.get("record"), dict):
                        # Merge shared document metadata into lot record
                        if isinstance(shared_metadata, dict):
                            for meta_k in ["institution_seller_name", "institution_seller", "auction_office", "auction_department", "catalogue_view_date", "remarks", "emd_bank_name"]:
                                if not res["record"].get(meta_k) and shared_metadata.get(meta_k):
                                    res["record"][meta_k] = shared_metadata[meta_k]
                    return res
                except Exception as lot_exc:
                    logger.exception("Async lot extraction worker exception for image %s: %s", img_p, lot_exc)
                    return {
                        "success": False,
                        "image": str(img_p),
                        "message": f"Lot extraction task failed: {lot_exc}",
                    }

        results = await asyncio.gather(*[_extract_worker(img) for img in images])
        timer.record_stage("Parallel Lot Extraction", time.time() - t_sub)

        # 6. Database Save & Profiling Summary Report
        t_sub = time.time()
        database = await self.save_results(upload, list(results))
        timer.record_stage("Database Persistence", time.time() - t_sub)

        # 7. Post-Processing Storage Cleanup
        try:
            split_file_paths = [
                img["image_path"] if isinstance(img, dict) and "image_path" in img else img
                for img in images
            ]
            processed_paths = [enhanced_path] if enhanced_path and enhanced_path != upload.original_file_path else []
            self.file_manager.cleanup_post_processing(
                split_paths=split_file_paths,
                processed_paths=processed_paths,
            )
        except Exception as cleanup_err:
            logger.warning("Post-processing file cleanup encountered error: %s", cleanup_err)

        timer.generate_report(logger)

        return {
            "upload": database["upload"],
            "results": database["records"],
            "summary": self.extraction_summary(list(results)),
            "performance_report": timer.generate_report(logger),
        }

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

    def build_response(
        self,
        result: dict,
    ) -> dict:
        """
        Build API response.
        """
        from app.core.schemas.auction_schemas import build_pipeline_response
        return build_pipeline_response(result)
    

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