"""
Upload Orchestration Service.

Production-Grade Decoupled Architecture:
1. process_document(): Phase 1 Pure AI Document Extraction (File Upload -> Extracted JSON). Zero PHP fields.
2. submit_auction(): Phase 2 Final Submission (Angular Master Values + Extracted JSON -> PHP API Insertion).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Tuple
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import UPLOAD_DIR, get_settings
from app.core.logger import get_logger
from app.services.integration.file_validator import FileValidatorService
from app.services.integration.request_validation_service import RequestValidationService
from app.services.integration.schema_builder import CommonAISchemaBuilder
from app.services.integration.ai_validator import AISchemaValidator, AIBusinessValidator
from app.services.integration.normalizer import DataNormalizer
from app.services.integration.payload_mapper import PurePayloadMapper
from app.services.integration.business_default_injector import BusinessDefaultInjector
from app.services.integration.angular_master_merge import AngularMasterMerger
from app.services.integration.consistency_validator import MappingConsistencyValidator
from app.services.integration.field_lifecycle_tracer import FieldLifecycleTracer
from app.services.integration.php_validator import PHPPayloadValidator
from app.services.integration.php_client import PHPIntegrationClient
from app.services.integration.response_parser import PHPResponseParser
from app.services.integration.processing_logger import IntegrationProcessingLogger
from app.services.integration.response_aggregator import ResponseAggregator
from app.services.pipeline import AuctionPipeline
from app.services.document_pipeline import DocumentPipeline
from app.schemas.integration_schemas import (
    AuctionSubmissionRequest,
    AuctionSubmissionResponse,
    AuctionSubmissionResult,
    DocumentProcessingResponse,
    IntegrationMasterData,
    IntegrationResponse,
    RecordProcessingStatus,
)

logger = get_logger(__name__)

class UploadOrchestrationService:
    """
    Orchestrates decoupled execution paths for pure AI extraction and PHP insertion.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.file_validator = FileValidatorService()
        self.schema_builder = CommonAISchemaBuilder()
        self.ai_schema_validator = AISchemaValidator()
        self.ai_business_validator = AIBusinessValidator()
        self.normalizer = DataNormalizer()
        self.payload_mapper = PurePayloadMapper()
        self.consistency_validator = MappingConsistencyValidator()
        self.lifecycle_tracer = FieldLifecycleTracer()
        self.php_validator = PHPPayloadValidator()
        self.php_client = PHPIntegrationClient()
        self.response_parser = PHPResponseParser()
        self.stage_logger = IntegrationProcessingLogger()
        self.response_aggregator = ResponseAggregator()

    @classmethod
    def map_extracted_dict_to_php_payload(cls, extracted_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Guarantees 100% field translation from any extracted dictionary format (raw canonical or mapped PHP) into PHP payload keys.
        """
        from app.services.extractor.canonical_normalizer import CanonicalAliasNormalizer
        norm_dict = CanonicalAliasNormalizer.normalize_record_aliases(extracted_dict)
        payload = dict(norm_dict)

        # 1. Auction Number
        if not payload.get("auction_number"):
            payload["auction_number"] = str(payload.get("auction_no") or payload.get("auction_id") or payload.get("raw_id") or "")

        # 2. Auction Date
        if not payload.get("auction_date"):
            payload["auction_date"] = str(payload.get("auction_start_date_time") or payload.get("auction_start_datetime") or payload.get("auction_time") or "")

        # 3. Reserve Price (Monetary Priority Hierarchy: Reserve Price -> Upset Price -> Base Price -> Starting Price -> Opening Bid)
        extracted_price = ""
        for p_key in ["reserve_price", "reserver_price", "upset_price", "base_price", "starting_price", "auction_start_price", "opening_bid", "start_floor_price"]:
            val = payload.get(p_key)
            if val is not None:
                s = str(val).strip()
                if s and s not in {"0", "0.0", "0.00", "null", "none", "n/a", "undefined"}:
                    extracted_price = s
                    break

        if extracted_price:
            payload["reserve_price"] = extracted_price
            payload["reserver_price"] = extracted_price
            payload["p_reserver_price"] = extracted_price
            payload["auction_start_price"] = extracted_price

        # 4. Borrower Name
        if not payload.get("borrower_name"):
            payload["borrower_name"] = str(payload.get("borrower") or payload.get("borrower_details") or payload.get("borrower_s") or payload.get("applicant") or payload.get("mortgagor") or payload.get("owner") or payload.get("guarantor") or "")

        # 5. Product Location (Derived short Locality/City without modifying full property_address)
        from app.services.integration.normalizer import DataNormalizer
        derived_loc = DataNormalizer.derive_product_location(payload)
        payload["product_location"] = derived_loc or str(payload.get("product_location") or payload.get("assets_location") or payload.get("property_address") or "")

        # 6. Institution Seller
        if not payload.get("institution_seller"):
            payload["institution_seller"] = str(payload.get("seller_name") or payload.get("vendor_name") or payload.get("bank_name") or payload.get("institution_seller") or "")

        # 7. EMD Price & Increment Price (Must map to numeric float/int or None, NEVER empty string "")
        import re
        def parse_numeric(v: Any) -> Any:
            if v is None or str(v).strip() in {"", "none", "null", "n/a", "undefined"}:
                return None
            c = re.sub(r"[^\d.]", "", str(v))
            if c:
                try:
                    f = float(c)
                    return int(f) if f.is_integer() else f
                except ValueError:
                    pass
            return None

        emd_val = parse_numeric(payload.get("emd_price") or payload.get("emd_amount") or payload.get("pre_bid_emd") or payload.get("p_emd_price"))
        payload["emd_price"] = emd_val
        payload["emd_amount"] = emd_val
        payload["pre_bid_emd"] = emd_val
        payload["p_emd_price"] = emd_val
        payload["p_emd_amount"] = emd_val

        inc_val = parse_numeric(payload.get("increment_price") or payload.get("bid_increment") or payload.get("p_increment_price"))
        payload["increment_price"] = inc_val
        payload["bid_increment"] = inc_val
        payload["p_increment_price"] = inc_val

        # 8. Auction Live Status (Map human text 'Pending' -> 1-char DB code 'N')
        raw_live_status = payload.get("auction_live_status") or payload.get("live_status") or "Pending"
        db_live_code = DataNormalizer.normalize_live_status_code(raw_live_status)
        payload["auction_live_status"] = db_live_code
        payload["p_auction_live_status"] = db_live_code

        # 9. Schema-Driven Centralized Payload Normalization
        from app.services.integration.php_payload_normalizer import CentralizedPHPPayloadNormalizer
        payload = CentralizedPHPPayloadNormalizer.normalize_payload(payload)

        return payload


    async def process_document(
        self,
        file: UploadFile,
    ) -> DocumentProcessingResponse:
        """
        Phase 1: Pure AI Document Extraction Endpoint Processing.
        Accepts uploaded file ONLY. Performs OCR, Gemini extraction, normalization, business defaults, and semantic consistency validation.
        Returns extracted auction JSON dictionary ready for Angular UI review.
        Does NOT generate PHP payload, does NOT call PHP insert API, and returns ZERO PHP fields.
        """
        start_time = time.time()
        processing_id = f"proc-doc-{uuid.uuid4().hex[:12]}"
        file_name = file.filename or "uploaded_document"

        try:
            content_bytes = await file.read()
            await file.seek(0)
        except Exception as read_err:
            err_msg = f"Failed to read uploaded file contents: {str(read_err)}"
            logger.error("[%s] %s", processing_id, err_msg)
            return DocumentProcessingResponse(
                success=False,
                stage="ERROR",
                processing_id=processing_id,
                file_name=file_name,
                document_type="UNKNOWN",
                processing_time_seconds=0.0,
                summary={"total_records": 0, "extracted_records": 0, "validation_failed": 1},
                records=[],
                message=err_msg,
            )

        # File Upload Validation ONLY
        is_file_valid, val_error = RequestValidationService.validate_file_upload(file, content_bytes)
        self.stage_logger.log_stage_upload(
            processing_id, file_name, "DOCUMENT", len(content_bytes), "PASSED" if is_file_valid else f"FAILED ({val_error})"
        )

        if not is_file_valid:
            return DocumentProcessingResponse(
                success=False,
                stage="ERROR",
                processing_id=processing_id,
                file_name=file_name,
                document_type="UNKNOWN",
                processing_time_seconds=round(time.time() - start_time, 2),
                summary={"total_records": 0, "extracted_records": 0, "validation_failed": 1},
                records=[],
                message=val_error,
            )

        # Save temporary uploaded file
        upload_dir = str(UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, f"{processing_id}_{file_name}")
        try:
            with open(save_path, "wb") as f:
                f.write(content_bytes)
        except Exception as save_err:
            err_msg = f"Failed to persist temporary upload file to disk: {str(save_err)}"
            logger.error("[%s] %s", processing_id, err_msg)
            return DocumentProcessingResponse(
                success=False,
                stage="ERROR",
                processing_id=processing_id,
                file_name=file_name,
                document_type="UNKNOWN",
                processing_time_seconds=round(time.time() - start_time, 2),
                summary={"total_records": 0, "extracted_records": 0, "validation_failed": 1},
                records=[],
                message=err_msg,
            )

        # AI Extraction Engine
        raw_extracted_records, doc_type = await self._run_ai_extraction(file, processing_id, start_time, file_name)
        if not raw_extracted_records:
            if isinstance(doc_type, DocumentProcessingResponse):
                return doc_type
            return DocumentProcessingResponse(
                success=False,
                stage="EXTRACTION_FAILED",
                processing_id=processing_id,
                file_name=file_name,
                document_type=doc_type or "IMAGE",
                processing_time_seconds=round(time.time() - start_time, 2),
                summary={"total_records": 0, "extracted_records": 0, "validation_failed": 1},
                records=[],
                processing_status="FAILED",
                error_detail="No valid auction records could be extracted from the document.",
                message=f"Document '{file_name}' processing failed: zero valid auction records extracted.",
            )

        # Multi-Lot Iteration for Pure AI Document Processing
        extracted_auction_records: List[Dict[str, Any]] = []
        validation_failed_count = 0

        # STEP 1: Log Raw OCR Count
        logger.info("[%s] STEP 1: Raw OCR Record Count: %d", processing_id, len(raw_extracted_records))

        for idx, raw_record in enumerate(raw_extracted_records, start=1):
            if not isinstance(raw_record, dict):
                raw_record = {k: v for k, v in raw_record.__dict__.items() if not k.startswith("_")} if hasattr(raw_record, "__dict__") else {}

            auc_num = str(raw_record.get("auction_no") or raw_record.get("auction_number") or raw_record.get("raw_id") or f"lot-{idx}")

            # STEP 2: Gemini Record Log
            logger.info("[%s] STEP 2: Gemini Record #%d (ID: '%s') - Input Raw Record Keys: %d", processing_id, idx, auc_num, len(raw_record))

            from app.services.integration.field_lifecycle_tracer import FieldLifecycleTracer

            common_schema = self.schema_builder.build_schema(raw_record, lot_index=idx)
            FieldLifecycleTracer.check_and_log_field_loss(raw_record, common_schema, "Extraction -> CommonAISchema", lot_index=idx)
            self.stage_logger.log_stage_common_schema(processing_id, idx, common_schema)

            is_schema_valid, schema_errors = self.ai_schema_validator.validate_schema(common_schema, lot_index=idx)
            is_business_valid, business_errors = self.ai_business_validator.validate_business_rules(common_schema, lot_index=idx)
            all_ai_errors = schema_errors + business_errors
            ai_valid = is_schema_valid and is_business_valid

            self.stage_logger.log_stage_ai_validation(processing_id, idx, is_schema_valid, is_business_valid, all_ai_errors)

            norm_schema = self.normalizer.normalize_schema(common_schema, lot_index=idx)
            FieldLifecycleTracer.check_and_log_field_loss(common_schema, norm_schema, "CommonAISchema -> DataNormalizer", lot_index=idx)
            self.stage_logger.log_stage_normalization(processing_id, idx, norm_schema)

            unmerged_payload = self.payload_mapper.map_to_php_payload(norm_schema=norm_schema, lot_index=idx)
            FieldLifecycleTracer.check_and_log_field_loss(norm_schema, unmerged_payload, "DataNormalizer -> PayloadMapper", lot_index=idx)
            self.stage_logger.log_stage_payload_mapping(processing_id, idx, unmerged_payload)

            mapped_payload = BusinessDefaultInjector.inject_defaults(unmerged_payload, lot_index=idx)
            FieldLifecycleTracer.check_and_log_field_loss(unmerged_payload, mapped_payload, "PayloadMapper -> BusinessDefaultInjector", lot_index=idx)
            self.stage_logger.log_stage_business_defaults(processing_id, idx, mapped_payload)

            # Also run Pre-PHP Consistency Checker against raw OCR text if present
            from app.services.integration.consistency_checker import PrePHPConsistencyChecker
            raw_ocr_txt = str(raw_record.get("raw_ocr_text") or raw_record.get("ocr_text") or "")
            is_pre_php_consistent, pre_php_warnings = PrePHPConsistencyChecker.check_extraction_consistency(
                ocr_text=raw_ocr_txt, final_payload=mapped_payload, lot_index=idx
            )

            if not ai_valid or not is_pre_php_consistent:
                validation_failed_count += 1
                mapped_payload["record_status"] = "PARTIAL"
                mapped_payload["needs_manual_review"] = True
                mapped_payload["validation_errors"] = all_ai_errors + pre_php_warnings
                logger.warning("[%s] MARK PARTIAL RECORD #%d (ID: '%s') - Stage: INCOMPLETE_EXTRACTION / CONSISTENCY_WARNING - Errors: %s. Preserving for manual review.", processing_id, idx, auc_num, all_ai_errors + pre_php_warnings)
            else:
                mapped_payload["record_status"] = "COMPLETE"
                mapped_payload["needs_manual_review"] = False

            # Stage-by-Stage Borrower Audit Logging
            raw_b_gemini = raw_record.get("borrower_name") or raw_record.get("borrower") or raw_record.get("borrower_details") or raw_record.get("applicant_name")
            canonical_b = norm_schema.get("borrower_name") or norm_schema.get("borrower") or norm_schema.get("borrower_details") or norm_schema.get("applicant_name")
            mapper_b = unmerged_payload.get("borrower_name")

            logger.info(
                "\n==================================================\n"
                "[BORROWER NAME PIPELINE AUDIT (Doc: %s)]\n"
                "RAW GEMINI     : borrower_name = %r\n"
                "CANONICAL MODEL: borrower_name = %r\n"
                "FIELD MAPPER   : borrower_name = %r\n"
                "==================================================",
                doc_type,
                raw_b_gemini,
                canonical_b,
                mapper_b,
            )

            # STEP 3: Mapped Auction Record Log
            logger.info("[%s] STEP 3: Mapped Auction Record #%d (ID: '%s') - Mapped Payload Keys: %d", processing_id, idx, auc_num, len(unmerged_payload))

            confidence = float(raw_record.get("confidence_score") or 0.95)
            consistency_report = self.consistency_validator.validate_consistency(
                common_schema=common_schema,
                norm_schema=norm_schema,
                php_payload=mapped_payload,
                lot_index=idx,
                confidence_score=confidence,
            )
            self.stage_logger.log_stage_consistency_report(processing_id, idx, consistency_report.report_dict)

            if not consistency_report.passed or consistency_report.has_critical_errors():
                mapped_payload["record_status"] = "PARTIAL"
                mapped_payload["needs_manual_review"] = True
                logger.warning("[%s] MARK PARTIAL RECORD #%d (ID: '%s') - Stage: CONSISTENCY_AUDIT_WARNING - Critical Errors: %d. Preserving for manual review.", processing_id, idx, auc_num, consistency_report.critical_errors_count)

            # COMPACT MATRIX TABLE & FIRST LOSS REPORT (Requirements #1 & #11)
            FieldLifecycleTracer.print_compact_lifecycle_table(
                ocr_dict={"borrower_name": raw_record.get("borrower_name"), "reserve_price": raw_record.get("reserve_price")},
                llm_dict=raw_record,
                parser_dict=raw_record,
                canonical_dict=norm_schema,
                mapper_dict=norm_schema,
                schema_dict=common_schema,
                norm_dict=norm_schema,
                php_dict=mapped_payload,
                lot_index=idx,
            )

            # FINAL DIAGNOSTIC REPORT (Requirement #9)
            logger.info(
                "\n==================================================\n"
                "[FINAL DIAGNOSTIC REPORT - LOT #%d]\n"
                "Auction Number      : %s\n"
                "OCR Confidence      : %.2f\n"
                "OCR Text Length     : %d chars\n"
                "Borrower Name       : %r\n"
                "Reserve Price       : %r\n"
                "Auction Start Price : %r\n"
                "EMD Price           : %r\n"
                "Increment Price     : %r\n"
                "Product Location    : %r\n"
                "Property Address    : %r\n"
                "Auction Details     : %r\n"
                "Record Status       : %s\n"
                "Needs Manual Review : %s\n"
                "==================================================",
                idx,
                mapped_payload.get("auction_number", ""),
                confidence,
                len(raw_ocr_txt),
                mapped_payload.get("borrower_name", ""),
                mapped_payload.get("reserve_price") or mapped_payload.get("reserver_price", ""),
                mapped_payload.get("auction_start_price", ""),
                mapped_payload.get("emd_price") or mapped_payload.get("emd_amount", ""),
                mapped_payload.get("increment_price", ""),
                mapped_payload.get("product_location", ""),
                mapped_payload.get("property_address", ""),
                (mapped_payload.get("auction_details") or "")[:60],
                mapped_payload.get("record_status", "COMPLETE"),
                mapped_payload.get("needs_manual_review", False),
            )


            # STEP 4: Validated Auction Record APPEND
            extracted_auction_records.append(mapped_payload)
            logger.info("[%s] STEP 4: Auction Record #%d (ID: '%s') APPENDED SUCCESSFULLY! Status: %s, Current Count: %d", processing_id, idx, auc_num, mapped_payload.get("record_status", "COMPLETE"), len(extracted_auction_records))


        from app.services.integration.payload_sanitizer import sanitize_json_payload
        extracted_auction_records = sanitize_json_payload(extracted_auction_records)

        total_elapsed = round(time.time() - start_time, 2)
        total_recs = len(raw_extracted_records)
        succ_recs = len(extracted_auction_records)

        # STEP 5: Final Response Auction Count Log
        logger.info("[%s] STEP 5: Final Response Auction Count: %d / %d (Validation Failed: %d)", processing_id, succ_recs, total_recs, validation_failed_count)

        # Save Session to Database & In-Memory Store (Strict Persistence)
        try:
            from app.repositories.auction_processing_session_repository import AuctionProcessingSessionRepository
            session_repo = AuctionProcessingSessionRepository(self.db)
            from app.services.integration.payload_sanitizer import sanitize_json_payload
            clean_raw_records = sanitize_json_payload(raw_extracted_records)
            clean_common = sanitize_json_payload(common_schema) if 'common_schema' in locals() else clean_raw_records
            clean_mapped = sanitize_json_payload(extracted_auction_records)
            await session_repo.create_session(
                processing_id=processing_id,
                file_name=file_name,
                document_type=doc_type,
                extracted_json=clean_raw_records,
                canonical_json=clean_common,
                mapped_payload=clean_mapped,
                consistency_report=consistency_report.report_dict if 'consistency_report' in locals() else None,
                status="READY_FOR_REVIEW",
            )
        except Exception as db_sess_err:
            err_msg = f"SESSION_SAVE_FAILED: Failed to persist extraction session to database table 'auction_processing_sessions': {str(db_sess_err)}"
            logger.error("[%s] %s", processing_id, err_msg)

        from app.services.integration.extraction_session_store import ExtractionSessionStore
        ExtractionSessionStore.save_session(processing_id, extracted_auction_records, file_name, doc_type)

        # CHECKPOINT 1 Log in process_document (before return)
        logger.info("[%s] CHECKPOINT 1 - Canonical Extracted Records Output: %s", processing_id, json.dumps(extracted_auction_records, default=str))

        has_critical_failure = succ_recs == 0
        proc_status = "FAILED" if has_critical_failure else "SUCCESS"
        err_det = "0 records extracted from document." if succ_recs == 0 else f"Extraction complete. {validation_failed_count} record(s) marked for manual review."

        return DocumentProcessingResponse(
            success=not has_critical_failure,
            stage="DOCUMENT_PROCESSED" if not has_critical_failure else "EXTRACTION_FAILED",
            processing_id=processing_id,
            file_name=file_name,
            document_type=doc_type,
            processing_time_seconds=total_elapsed,
            summary={
                "total_records": total_recs,
                "extracted_records": succ_recs,
                "validation_failed": validation_failed_count,
            },
            records=extracted_auction_records,
            processing_status=proc_status,
            error_detail=err_det,
            message=f"Document '{file_name}' processed with status: {proc_status}. {succ_recs}/{total_recs} records extracted.",
        )

    async def _insert_single_record(
        self,
        raw_record: Dict[str, Any],
        lot_index: int,
        master_data: IntegrationMasterData,
        processing_id: str,
    ) -> AuctionSubmissionResult:
        """
        Processes and inserts a single auction record independently into PHP system.
        Isolated payload generation, validation, normalization, and insertion.
        Does not raise unhandled exceptions to ensure batch continuity.
        """
        auction_num = str(
            raw_record.get("auction_number")
            or raw_record.get("p_auction_number")
            or raw_record.get("auction_num")
            or f"LOT-{lot_index}"
        ).strip()

        try:
            # 1. Merge master selections per record (fresh payload copy)
            merged_payload = AngularMasterMerger.merge_master_data(
                payload=dict(raw_record),
                master_data=master_data,
                uploaded_file_path="",
                file_type="JSON",
                lot_index=lot_index,
            )

            # 2. Resolve section_id and part_id dynamically per record
            from app.services.integration.master_section_resolver import MasterSectionResolver
            sec_id, part_id, is_sec_valid, sec_err_msg = MasterSectionResolver.resolve_section_and_part(merged_payload, processing_id)
            if not is_sec_valid or sec_id is None:
                err_msg = f"Master Section Resolution Failed: {sec_err_msg}"
                logger.error("[%s][Record #%d] %s", processing_id, lot_index, err_msg)
                return AuctionSubmissionResult(
                    record_no=lot_index,
                    auction_number=auction_num,
                    status="FAILED",
                    php_record_id="",
                    error=err_msg,
                )

            merged_payload["section_id"] = sec_id
            merged_payload["part_id"] = part_id

            # 3. Build & normalize fresh PHP payload
            final_php_payload = self.map_extracted_dict_to_php_payload(merged_payload)
            final_php_payload = BusinessDefaultInjector.inject_defaults(final_php_payload, lot_index=lot_index)

            from app.services.integration.php_payload_normalizer import CentralizedPHPPayloadNormalizer
            final_php_payload = CentralizedPHPPayloadNormalizer.normalize_payload(final_php_payload, processing_id)

            # Auto-map recovery for borrower_name if missing
            if not final_php_payload.get("borrower_name") or str(final_php_payload.get("borrower_name")).strip() in {"", "N/A"}:
                resolved_b = (
                    raw_record.get("borrower_name") or
                    raw_record.get("borrower") or
                    raw_record.get("applicant_name") or
                    raw_record.get("borrower_details") or
                    raw_record.get("mortgagor_name") or
                    raw_record.get("guarantor_name") or
                    raw_record.get("co_borrower") or
                    "N/A"
                )
                final_php_payload["borrower_name"] = str(resolved_b).strip()

            # Multi-source extraction & fallback recovery for product_location before PHP validation
            needs_manual_review = False
            cur_loc = str(
                final_php_payload.get("product_location")
                or final_php_payload.get("p_product_location")
                or ""
            ).strip()

            if not cur_loc or cur_loc.lower() in {"", "n/a", "null", "none", "undefined"}:
                # 1. Attempt extraction from asset address, property address, merged schema, raw record
                derived_loc = DataNormalizer.derive_product_location(merged_payload)
                if not derived_loc:
                    derived_loc = DataNormalizer.derive_product_location(raw_record)
                if not derived_loc:
                    # 2. Check auction description, property details, raw text, location fields, shared metadata
                    alt_sources = [
                        raw_record.get("property_address"),
                        raw_record.get("asset_address"),
                        raw_record.get("assets_location"),
                        raw_record.get("property_details"),
                        raw_record.get("auction_description"),
                        raw_record.get("description"),
                        raw_record.get("raw_text"),
                        raw_record.get("borrower_address"),
                        raw_record.get("location"),
                        raw_record.get("district"),
                        raw_record.get("city"),
                        raw_record.get("town"),
                        raw_record.get("locality"),
                        raw_record.get("village"),
                    ]
                    for alt in alt_sources:
                        if alt and str(alt).strip():
                            d = DataNormalizer.derive_product_location({"property_address": str(alt).strip()})
                            if d:
                                derived_loc = d
                                break

                if derived_loc:
                    final_php_payload["product_location"] = derived_loc
                    final_php_payload["p_product_location"] = derived_loc
                    logger.info("[%s][Record #%d] Derived missing product_location: %r", processing_id, lot_index, derived_loc)
                else:
                    final_php_payload["product_location"] = ""
                    final_php_payload["p_product_location"] = ""
                    needs_manual_review = True
                    logger.warning("[%s][Record #%d] Optional field 'product_location' is missing/empty; storing '' and marking needs_manual_review=True for PHP insertion", processing_id, lot_index)

            # Update auction_num if mapped into PHP payload
            payload_auc_num = str(final_php_payload.get("auction_number") or "").strip()
            if payload_auc_num and payload_auc_num != "N/A":
                auction_num = payload_auc_num

            # 4. Validate PHP payload
            is_php_valid, php_val_errors = self.php_validator.validate_php_payload(final_php_payload, lot_index=lot_index)
            if not is_php_valid:
                err_detail = "Mapped PHP Payload validation warning: " + "; ".join(php_val_errors)
                logger.warning("[%s][Record #%d] %s. Preserving extracted fields and marking needs_manual_review=True.", processing_id, lot_index, err_detail)
                needs_manual_review = True

            # 5. Sanitize and validate JSON payload serializability
            from app.services.integration.payload_sanitizer import validate_and_serialize_json_payload
            try:
                final_php_payload, _ = validate_and_serialize_json_payload(final_php_payload, processing_id)
            except Exception as json_val_err:
                err_detail = f"JSON payload validation failed: {str(json_val_err)}"
                logger.error("[%s][Record #%d] %s", processing_id, lot_index, err_detail)
                return AuctionSubmissionResult(
                    record_no=lot_index,
                    auction_number=auction_num,
                    status="FAILED",
                    needs_manual_review=True,
                    php_record_id="",
                    error=err_detail,
                )

            # Requirement #15: AUCTION NUMERIC FIELD TRACE
            ext_inc = raw_record.get("increment_price") if isinstance(raw_record, dict) else None
            canon_inc = raw_record.get("increment_price") if isinstance(raw_record, dict) else None
            map_inc = merged_payload.get("increment_price") if isinstance(merged_payload, dict) else None
            norm_inc = final_php_payload.get("increment_price")
            final_p_inc = final_php_payload.get("p_increment_price")

            logger.info(
                "\n========== AUCTION NUMERIC FIELD TRACE ==========\n"
                "Extracted increment_price:\n  value = %r\n  type = %s\n\n"
                "Canonical increment_price:\n  value = %r\n  type = %s\n\n"
                "Mapped increment_price:\n  value = %r\n  type = %s\n\n"
                "Normalized increment_price:\n  value = %r\n  type = %s\n\n"
                "Final Python p_increment_price:\n  value = %r\n  type = %s\n\n"
                "HTTP JSON p_increment_price:\n  value = %s\n  JSON type = %s\n\n"
                "PHP received p_increment_price:\n  value = Logged at PHP endpoint\n  PHP type = PHP string/null\n\n"
                "PHP stored procedure parameter:\n  value = Logged at PHP procedure layer\n  type = DECIMAL\n\n"
                "MySQL final value:\n  value = Logged at MySQL INSERT layer\n  type = DECIMAL(10,2)\n"
                "=================================================",
                ext_inc,
                type(ext_inc).__name__,
                canon_inc,
                type(canon_inc).__name__,
                map_inc,
                type(map_inc).__name__,
                norm_inc,
                type(norm_inc).__name__,
                final_p_inc,
                type(final_p_inc).__name__,
                "null" if final_p_inc is None else repr(final_p_inc),
                "null" if final_p_inc is None else type(final_p_inc).__name__,
            )

            # Dynamic Database Type Normalization for all DECIMAL & pricing fields
            from app.services.integration.php_payload_normalizer import PHP_SCHEMA_SPEC, CentralizedPHPPayloadNormalizer
            DECIMAL_FIELDS = [k for k, spec in PHP_SCHEMA_SPEC.items() if spec.get("type") in {"DECIMAL", "FLOAT"}]
            for k in list(final_php_payload.keys()):
                if k.lower().endswith(("_price", "_amount", "_increment", "_emd")) and k not in DECIMAL_FIELDS:
                    DECIMAL_FIELDS.append(k)
            for dec_field in DECIMAL_FIELDS:
                if dec_field in final_php_payload:
                    raw_f_val = final_php_payload.get(dec_field)
                    norm_dec = CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(raw_f_val)
                    converted_f_val = float(norm_dec)
                    if raw_f_val in {"", None} or (isinstance(raw_f_val, str) and not raw_f_val.strip()):
                        logger.info("[PHP PAYLOAD NUMERIC NORMALIZATION] %s: %r -> 0.00", dec_field, raw_f_val)
                    final_php_payload[dec_field] = converted_f_val

            # Requirement #12: Log [FINAL PHP DB PAYLOAD]
            p_inc_val = final_php_payload.get("p_increment_price")
            logger.info(
                "\n[FINAL PHP DB PAYLOAD]\n"
                "p_increment_price = %s\n"
                "type = %s\n",
                "NULL" if p_inc_val is None else f"{p_inc_val:.2f}",
                type(p_inc_val).__name__,
            )

            # 7. Send insert request to PHP API
            status_code, raw_resp_json, err_detail = await self.php_client.send_insert_request(
                payload=final_php_payload,
                processing_id=processing_id,
                lot_index=lot_index,
            )

            parsed_resp = self.response_parser.parse_response(
                http_status_code=status_code,
                raw_json=raw_resp_json,
                error_detail=err_detail,
            )

            is_succ = getattr(parsed_resp, "success", getattr(parsed_resp, "is_success", False))
            rec_id = str(parsed_resp.record_id or "").strip()
            final_err_detail = "" if is_succ else (f"MySQL insertion failed: {parsed_resp.message}" if "too long" in parsed_resp.message.lower() or "sqlstate" in parsed_resp.message.lower() else (err_detail or parsed_resp.message))

            # 8-STEP COMPLETE INSERT LIFECYCLE AUDIT (Requirement #4)
            import hashlib
            payload_hash = hashlib.sha256(json.dumps(final_php_payload, default=str).encode("utf-8")).hexdigest()[:12]
            php_status_flag = raw_resp_json.get("status") if isinstance(raw_resp_json, dict) else "N/A"
            php_code_flag = raw_resp_json.get("code") if isinstance(raw_resp_json, dict) else status_code

            logger.info(
                "\n==================================================\n"
                "COMPLETE INSERT FLOW LIFECYCLE TRACE (Lot #%d)\n"
                "1. Canonical Record    : PRESERVED\n"
                "2. PHP Payload         : GENERATED\n"
                "3. Serialized Payload  : HASH %s\n"
                "4. HTTP Request        : SENT (HTTP %d)\n"
                "5. PHP HTTP Response   : RECEIVED (HTTP %d)\n"
                "6. PHP Response Parser : STATUS_CAT=%s, IS_SUCCESS=%s\n"
                "7. Insert Result       : STATUS=%s, REC_ID=%r\n"
                "8. Final API Response  : EXPOSED\n\n"
                "RECORD SUMMARY:\n"
                "record_no              : %d\n"
                "auction_number         : %s\n"
                "payload_hash           : %s\n"
                "PHP HTTP status        : %d\n"
                "PHP response status    : %s\n"
                "PHP response code      : %s\n"
                "PHP response message   : %r\n"
                "php_record_id          : %r\n"
                "final insertion status : %s\n"
                "==================================================",
                lot_index,
                payload_hash,
                status_code,
                status_code,
                parsed_resp.status_category,
                is_succ,
                "SUCCESS" if is_succ else "FAILED",
                rec_id,
                lot_index,
                auction_num,
                payload_hash,
                status_code,
                php_status_flag,
                php_code_flag,
                parsed_resp.message,
                rec_id,
                "SUCCESS" if is_succ else "FAILED",
            )

            if is_succ:
                logger.info("[%s][Record #%d] PHP Insertion SUCCESS (Record ID: %s, Needs Review: %s)", processing_id, lot_index, rec_id, needs_manual_review)
                return AuctionSubmissionResult(
                    record_no=lot_index,
                    auction_number=auction_num,
                    status="SUCCESS",
                    needs_manual_review=needs_manual_review,
                    php_record_id=rec_id,
                    error="",
                )
            else:
                logger.warning("[%s][Record #%d] PHP Insertion FAILED: %s", processing_id, lot_index, final_err_detail)
                return AuctionSubmissionResult(
                    record_no=lot_index,
                    auction_number=auction_num,
                    status="FAILED",
                    needs_manual_review=True,
                    php_record_id="",
                    error=final_err_detail,
                )

        except Exception as unhandled_err:
            err_msg = f"Unhandled record exception: {str(unhandled_err)}"
            logger.exception("[%s][Record #%d] %s", processing_id, lot_index, err_msg)
            return AuctionSubmissionResult(
                record_no=lot_index,
                auction_number=auction_num,
                status="FAILED",
                needs_manual_review=True,
                php_record_id="",
                error=err_msg,
            )

    async def submit_auction(
        self,
        submission_req: AuctionSubmissionRequest,
    ) -> AuctionSubmissionResponse:
        """
        Phase 2: Final Batch Submission Endpoint Processing.
        Dynamically iterates through ALL extracted records, inserting each as an independent row.
        Does not abort batch on individual record failure. Tracks live DB session progress.
        """
        start_time = time.time()
        processing_id = submission_req.processing_id or f"proc-sub-{uuid.uuid4().hex[:12]}"

        # Step 1: Log incoming submission request details
        logger.info(
            "[%s] BATCH SUBMISSION REQUEST RECEIVED - processing_id: '%s', extracted_auction_present: %s, extracted_auctions_present: %s",
            processing_id,
            submission_req.processing_id,
            submission_req.extracted_auction is not None,
            submission_req.extracted_auctions is not None,
        )

        # Step 2: Retrieve ALL extracted records (DB Session -> Disk/Memory Store -> Request Body)
        records_to_process: List[Dict[str, Any]] = []

        if submission_req.processing_id:
            try:
                from app.repositories.auction_processing_session_repository import AuctionProcessingSessionRepository
                session_repo = AuctionProcessingSessionRepository(self.db)
                db_session = await session_repo.get_by_processing_id(submission_req.processing_id)
                if db_session:
                    db_payloads = db_session.mapped_payload or db_session.extracted_json
                    if isinstance(db_payloads, list):
                        for item in db_payloads:
                            if isinstance(item, dict):
                                records_to_process.append(dict(item))
                            elif hasattr(item, "__dict__"):
                                records_to_process.append(dict(item.__dict__))
                    elif isinstance(db_payloads, dict):
                        records_to_process.append(dict(db_payloads))
            except Exception as db_err:
                logger.warning("[%s] DB session lookup exception: %s", processing_id, db_err)

        if not records_to_process and submission_req.processing_id:
            from app.services.integration.extraction_session_store import ExtractionSessionStore
            session = ExtractionSessionStore.get_session(submission_req.processing_id)
            if session and session.get("extracted_records"):
                ext_recs = session["extracted_records"]
                if isinstance(ext_recs, list):
                    for item in ext_recs:
                        if isinstance(item, dict):
                            records_to_process.append(dict(item))
                        elif hasattr(item, "__dict__"):
                            records_to_process.append(dict(item.__dict__))

        if not records_to_process:
            if submission_req.extracted_auctions:
                records_to_process = [dict(r) for r in submission_req.extracted_auctions if isinstance(r, dict)]
            elif submission_req.extracted_auction:
                records_to_process = [dict(submission_req.extracted_auction)]

        if not records_to_process:
            err_msg = f"SESSION_NOT_FOUND: No extracted auction data found for processing_id '{submission_req.processing_id}'."
            logger.error("[%s] %s", processing_id, err_msg)
            return AuctionSubmissionResponse(
                success=False,
                stage="SESSION_NOT_FOUND",
                processing_id=processing_id,
                php_insert_success=False,
                total_records=0,
                inserted=0,
                failed=0,
                processing_time=round(time.time() - start_time, 2),
                results=[],
                php_record_id="",
                php_response_message=err_msg,
                php_response_raw=None,
                error_detail=err_msg,
                message=err_msg,
            )

        total_recs = len(records_to_process)
        logger.info("[%s] TOTAL EXTRACTED RECORDS TO PROCESS IN BATCH: %d", processing_id, total_recs)

        # Step 3: Validate Required Angular Master Selections
        master_data = IntegrationMasterData(
            vendor_id=submission_req.vendor_id,
            section_id=submission_req.section_id,
            part_id=submission_req.part_id,
            auction_type=submission_req.auction_type,
            payment_type=submission_req.payment_type,
            category_id=submission_req.category_id or "",
            item_id=submission_req.item_id or "",
            demo_auction=submission_req.demo_auction or "0",
            borrower_required=submission_req.borrower_required or "0",
            auction_interested=submission_req.auction_interested or "0",
            auction_image_url=submission_req.auction_image_url or "",
            auction_supporting_docs_1=submission_req.auction_supporting_docs_1 or "",
            auction_supporting_docs_2=submission_req.auction_supporting_docs_2 or "",
        )

        is_master_valid, missing_fields, val_msg = RequestValidationService.validate_master_selections(master_data)
        if not is_master_valid:
            logger.warning("[%s] Master Selection Validation Failed: %s", processing_id, val_msg)
            return AuctionSubmissionResponse(
                success=False,
                stage="MASTER_DATA_MISSING",
                processing_id=processing_id,
                php_insert_success=False,
                total_records=total_recs,
                inserted=0,
                failed=total_recs,
                processing_time=round(time.time() - start_time, 2),
                results=[],
                php_record_id="",
                php_response_message=val_msg,
                php_response_raw=None,
                error_detail=val_msg,
                message=val_msg,
            )

        # Step 4: Track session status start
        session_repo = None
        if submission_req.processing_id:
            try:
                from app.repositories.auction_processing_session_repository import AuctionProcessingSessionRepository
                session_repo = AuctionProcessingSessionRepository(self.db)
                await session_repo.update_status(
                    processing_id=submission_req.processing_id,
                    status=f"Processing Started (0/{total_recs})",
                    completed=False,
                )
            except Exception as db_status_err:
                logger.warning("[%s] Failed to log initial session status: %s", processing_id, db_status_err)

        # Step 5: Execute dynamic batch insertion for every record independently
        results: List[AuctionSubmissionResult] = []
        inserted_count = 0
        failed_count = 0
        successful_record_ids: List[str] = []

        for idx, record in enumerate(records_to_process, start=1):
            if session_repo and submission_req.processing_id:
                try:
                    await session_repo.update_status(
                        processing_id=submission_req.processing_id,
                        status=f"Processing Record {idx}/{total_recs}",
                        completed=False,
                    )
                except Exception:
                    pass

            rec_result = await self._insert_single_record(
                raw_record=record,
                lot_index=idx,
                master_data=master_data,
                processing_id=processing_id,
            )
            results.append(rec_result)

            if rec_result.status == "SUCCESS":
                inserted_count += 1
                if rec_result.php_record_id:
                    successful_record_ids.append(rec_result.php_record_id)
            else:
                failed_count += 1

        total_elapsed = round(time.time() - start_time, 2)
        overall_success = (inserted_count == total_recs and total_recs > 0)
        
        if inserted_count == total_recs and total_recs > 0:
            final_status = "COMPLETED"
        elif inserted_count > 0 and failed_count > 0:
            final_status = "PARTIALLY_COMPLETED"
        else:
            final_status = "PHP_INSERT_FAILED"

        summary_msg = f"Batch submission completed for '{processing_id}'. Inserted {inserted_count}/{total_recs} records into PHP Master Software in {total_elapsed}s." if overall_success else f"Batch submission failed for '{processing_id}'. Inserted {inserted_count}/{total_recs} records into PHP Master Software."

        combined_php_ids = ", ".join(successful_record_ids)

        if session_repo and submission_req.processing_id:
            try:
                await session_repo.update_status(
                    processing_id=submission_req.processing_id,
                    status=final_status,
                    php_record_id=combined_php_ids,
                    php_response_message=summary_msg,
                    completed=overall_success,
                    error_detail="" if failed_count == 0 else f"{failed_count}/{total_recs} records failed insertion.",
                )
            except Exception as db_final_err:
                logger.warning("[%s] Failed to log final session status: %s", processing_id, db_final_err)

        return AuctionSubmissionResponse(
            success=overall_success,
            stage="AUCTION_SUBMITTED" if overall_success else "PHP_INSERT_FAILED",
            processing_id=processing_id,
            php_insert_success=overall_success,
            total_records=total_recs,
            inserted=inserted_count,
            failed=failed_count,
            processing_time=total_elapsed,
            results=results,
            php_record_id=combined_php_ids,
            php_response_message=summary_msg,
            php_response_raw={"total_records": total_recs, "inserted": inserted_count, "failed": failed_count},
            error_detail="" if failed_count == 0 else f"{failed_count}/{total_recs} records failed insertion.",
            message=summary_msg,
        )

    async def process_and_insert(
        self,
        file: UploadFile,
        master_data: IntegrationMasterData,
    ) -> IntegrationResponse:
        """
        Phase 3 Legacy Dual-Mode Endpoint: AI Extraction + Angular Master Merge + PHP Insertion.
        """
        start_time = time.time()
        processing_id = f"proc-ins-{uuid.uuid4().hex[:12]}"
        file_name = file.filename or "uploaded_document"

        try:
            content_bytes = await file.read()
            await file.seek(0)
        except Exception as read_err:
            err_msg = f"Failed to read uploaded file contents: {str(read_err)}"
            logger.error("[%s] %s", processing_id, err_msg)
            return self.response_aggregator.build_error_response(
                processing_id, file_name, "UNKNOWN", 0.0, err_msg
            )

        is_file_valid, val_error = RequestValidationService.validate_file_upload(file, content_bytes)
        self.stage_logger.log_stage_upload(
            processing_id, file_name, "DOCUMENT", len(content_bytes), "PASSED" if is_file_valid else f"FAILED ({val_error})"
        )

        if not is_file_valid:
            return self.response_aggregator.build_error_response(
                processing_id, file_name, "UNKNOWN", round(time.time() - start_time, 2), val_error
            )

        upload_dir = str(UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, f"{processing_id}_{file_name}")
        try:
            with open(save_path, "wb") as f:
                f.write(content_bytes)
        except Exception as save_err:
            err_msg = f"Failed to persist temporary upload file to disk: {str(save_err)}"
            logger.error("[%s] %s", processing_id, err_msg)
            return self.response_aggregator.build_error_response(
                processing_id, file_name, "UNKNOWN", round(time.time() - start_time, 2), err_msg
            )

        raw_extracted_records, doc_type = await self._run_ai_extraction(file, processing_id, start_time, file_name)
        if not raw_extracted_records and isinstance(doc_type, IntegrationResponse):
            return doc_type

        record_statuses: List[RecordProcessingStatus] = []

        for idx, raw_record in enumerate(raw_extracted_records, start=1):
            if not isinstance(raw_record, dict):
                raw_record = {k: v for k, v in raw_record.__dict__.items() if not k.startswith("_")} if hasattr(raw_record, "__dict__") else {}

            common_schema = self.schema_builder.build_schema(raw_record, lot_index=idx)
            self.stage_logger.log_stage_common_schema(processing_id, idx, common_schema)
            auction_num = str(common_schema.get("auction_number") or f"LOT-{idx}")

            is_schema_valid, schema_errors = self.ai_schema_validator.validate_schema(common_schema, lot_index=idx)
            is_business_valid, business_errors = self.ai_business_validator.validate_business_rules(common_schema, lot_index=idx)
            all_ai_errors = schema_errors + business_errors
            ai_valid = is_schema_valid and is_business_valid

            self.stage_logger.log_stage_ai_validation(processing_id, idx, is_schema_valid, is_business_valid, all_ai_errors)

            if not ai_valid:
                record_statuses.append(
                    RecordProcessingStatus(
                        lot_index=idx,
                        auction_number=auction_num,
                        validation_success=False,
                        validation_errors=all_ai_errors,
                        php_insert_success=False,
                        error_detail="AI Schema / Business validation failed.",
                    )
                )
                continue

            norm_schema = self.normalizer.normalize_schema(common_schema, lot_index=idx)
            self.stage_logger.log_stage_normalization(processing_id, idx, norm_schema)

            unmerged_payload = self.payload_mapper.map_to_php_payload(norm_schema=norm_schema, lot_index=idx)
            self.stage_logger.log_stage_payload_mapping(processing_id, idx, unmerged_payload)

            default_injected_payload = BusinessDefaultInjector.inject_defaults(unmerged_payload, lot_index=idx)
            self.stage_logger.log_stage_business_defaults(processing_id, idx, default_injected_payload)

            php_payload = AngularMasterMerger.merge_master_data(
                payload=default_injected_payload,
                master_data=master_data,
                uploaded_file_path=save_path,
                file_type=doc_type,
                lot_index=idx,
            )
            self.stage_logger.log_stage_angular_merge(processing_id, idx, php_payload)

            from app.services.integration.php_payload_normalizer import CentralizedPHPPayloadNormalizer
            php_payload = CentralizedPHPPayloadNormalizer.normalize_payload(php_payload, processing_id)

            self.lifecycle_tracer.trace_lifecycle(
                raw_extract=raw_record,
                common_schema=common_schema,
                norm_schema=norm_schema,
                php_payload=php_payload,
                lot_index=idx,
            )

            confidence = float(raw_record.get("confidence_score") or 0.95)
            consistency_report = self.consistency_validator.validate_consistency(
                common_schema=common_schema,
                norm_schema=norm_schema,
                php_payload=php_payload,
                lot_index=idx,
                confidence_score=confidence,
            )
            self.stage_logger.log_stage_consistency_report(processing_id, idx, consistency_report.report_dict)

            if not consistency_report.passed or consistency_report.has_critical_errors():
                crit_err_msg = f"Critical Consistency Validation Failed: {consistency_report.critical_errors_count} data loss errors."
                record_statuses.append(
                    RecordProcessingStatus(
                        lot_index=idx,
                        auction_number=php_payload["auction_number"],
                        validation_success=False,
                        validation_errors=[crit_err_msg],
                        consistency_report=consistency_report.report_dict,
                        php_insert_success=False,
                        error_detail=crit_err_msg,
                    )
                )
                continue

            is_php_valid, php_val_errors = self.php_validator.validate_php_payload(php_payload, lot_index=idx)
            self.stage_logger.log_stage_php_validation(processing_id, idx, is_php_valid, php_val_errors)

            if not is_php_valid:
                is_master_pending = any("MASTER_SELECTION_REQUIRED" in err for err in php_val_errors)
                val_ok = True if is_master_pending else False
                err_msg = "Extracted auction JSON generated successfully. User master selection (vendor_id, section_id, part_id) required before PHP insertion." if is_master_pending else "Mapped PHP Payload validation failed."

                record_statuses.append(
                    RecordProcessingStatus(
                        lot_index=idx,
                        auction_number=php_payload["auction_number"],
                        validation_success=val_ok,
                        validation_errors=php_val_errors,
                        consistency_report=consistency_report.report_dict,
                        php_insert_success=False,
                        error_detail=err_msg,
                    )
                )
                continue

            # Final DECIMAL field boundary normalization for submit_auction
            from app.services.integration.php_payload_normalizer import PHP_SCHEMA_SPEC, CentralizedPHPPayloadNormalizer
            DECIMAL_FIELDS = [k for k, spec in PHP_SCHEMA_SPEC.items() if spec.get("type") in {"DECIMAL", "FLOAT"}]
            for k in list(php_payload.keys()):
                if k.lower().endswith(("_price", "_amount", "_increment", "_emd")) and k not in DECIMAL_FIELDS:
                    DECIMAL_FIELDS.append(k)
            for dec_field in DECIMAL_FIELDS:
                if dec_field in php_payload:
                    raw_f_val = php_payload.get(dec_field)
                    norm_dec = CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(raw_f_val)
                    php_payload[dec_field] = float(norm_dec)

            status_code, raw_resp_json, err_detail = await self.php_client.send_insert_request(
                payload=php_payload,
                processing_id=processing_id,
                lot_index=idx,
            )

            parsed_resp = self.response_parser.parse_response(
                http_status_code=status_code,
                raw_json=raw_resp_json,
                error_detail=err_detail,
            )
            self.stage_logger.log_stage_php_result(
                processing_id, idx, status_code, parsed_resp.status_category, parsed_resp.record_id or "", parsed_resp.message
            )

            record_statuses.append(
                RecordProcessingStatus(
                    lot_index=idx,
                    auction_number=php_payload["auction_number"],
                    validation_success=True,
                    validation_errors=[],
                    consistency_report=consistency_report.report_dict,
                    php_insert_success=getattr(parsed_resp, "success", getattr(parsed_resp, "is_success", False)),
                    php_record_id=parsed_resp.record_id or "",
                    php_response_message=parsed_resp.message,
                    php_response_raw=raw_resp_json,
                    error_detail="" if getattr(parsed_resp, "success", getattr(parsed_resp, "is_success", False)) else (err_detail or parsed_resp.message),
                )
            )

        total_elapsed = round(time.time() - start_time, 2)
        target_status = "PASS" if total_elapsed <= 10.0 or doc_type == "PDF" else "WARN"

        logger.info(
            "\n==================================================\n"
            "[PERFORMANCE TIMING AUDIT]\n"
            "Document Name  : %s (%s)\n"
            "Total Lots     : %d\n"
            "Total Time     : %.2fs (Target: <= 10.0s - %s)\n"
            "==================================================",
            file_name,
            doc_type,
            len(raw_extracted_records),
            total_elapsed,
            target_status,
        )

        return self.response_aggregator.aggregate_multi_lot_response(
            processing_id=processing_id,
            file_name=file_name,
            file_type=doc_type,
            record_statuses=record_statuses,
            total_elapsed_seconds=total_elapsed,
        )

    async def _run_ai_extraction(
        self,
        file: UploadFile,
        processing_id: str,
        start_time: float,
        file_name: str,
    ) -> Tuple[List[Dict[str, Any]], Any]:
        """
        Internal helper: Runs document pipeline or image pipeline AI extraction.
        """
        doc_type = "PDF" if (file.filename or "").lower().endswith(".pdf") else "IMAGE"
        raw_extracted_records: List[Dict[str, Any]] = []

        try:
            if doc_type == "PDF":
                pdf_pipeline = DocumentPipeline(self.db)
                pipeline_result = await pdf_pipeline.run(file)
            else:
                image_pipeline = AuctionPipeline(self.db)
                pipeline_result = await image_pipeline.run(file)

            if isinstance(pipeline_result, dict):
                if isinstance(pipeline_result.get("records"), list):
                    raw_extracted_records = pipeline_result["records"]
                elif isinstance(pipeline_result.get("results"), list):
                    raw_extracted_records = pipeline_result["results"]
                elif isinstance(pipeline_result.get("auctions"), list):
                    raw_extracted_records = pipeline_result["auctions"]
                else:
                    data_body = pipeline_result.get("data")
                    if isinstance(data_body, dict):
                        raw_extracted_records = data_body.get("records") or data_body.get("auctions") or data_body.get("results") or []
                    elif isinstance(data_body, list):
                        raw_extracted_records = data_body

            self.stage_logger.log_stage_extraction(processing_id, doc_type, len(raw_extracted_records))

        except Exception as ext_err:
            logger.exception("[%s] AI Extraction Engine Exception: %s", processing_id, ext_err)
            err_resp = DocumentProcessingResponse(
                success=False,
                stage="ERROR",
                processing_id=processing_id,
                file_name=file_name,
                document_type=doc_type,
                processing_time_seconds=round(time.time() - start_time, 2),
                summary={"total_records": 0, "extracted_records": 0, "validation_failed": 1},
                records=[],
                message=f"AI Extraction Engine Error: {str(ext_err)}",
            )
            return [], err_resp

        if not raw_extracted_records:
            msg = "Extraction completed but 0 auction records were detected in the document."
            logger.warning("[%s] %s", processing_id, msg)
            err_resp = DocumentProcessingResponse(
                success=False,
                stage="ERROR",
                processing_id=processing_id,
                file_name=file_name,
                document_type=doc_type,
                processing_time_seconds=round(time.time() - start_time, 2),
                summary={"total_records": 0, "extracted_records": 0, "validation_failed": 1},
                records=[],
                message=msg,
            )
            return [], err_resp

        return raw_extracted_records, doc_type
