"""
Processing Logger.

Centralized structured logger providing explicit visual stage banner outputs for end-to-end auditability.
"""

from __future__ import annotations

from typing import Any, Dict
from app.core.logger import get_logger

logger = get_logger(__name__)

class IntegrationProcessingLogger:
    """
    Formatted stage logger outputting clear visual banners for all 8 pipeline stages.
    """

    @staticmethod
    def log_stage_upload(processing_id: str, file_name: str, doc_type: str, file_size: int, status: str) -> None:
        logger.info(
            "\n========== FILE UPLOAD & VALIDATION ==========\n"
            "Processing ID : %s\n"
            "File Name     : %s\n"
            "Type Detected : %s\n"
            "File Size     : %d bytes\n"
            "Validation    : %s\n"
            "==============================================",
            processing_id, file_name, doc_type, file_size, status
        )

    @staticmethod
    def log_stage_request_validation(processing_id: str, valid: bool, missing_fields: list[str], message: str) -> None:
        logger.info(
            "\n========== REQUEST VALIDATION ==========\n"
            "Processing ID    : %s\n"
            "Validation Status: %s\n"
            "Missing Inputs   : %s\n"
            "Message          : %s\n"
            "========================================",
            processing_id,
            "PASSED" if valid else "FAILED",
            missing_fields if missing_fields else "None",
            message,
        )

    @staticmethod
    def log_stage_extraction(processing_id: str, doc_type: str, lot_count: int) -> None:
        logger.info(
            "\n========== AI EXTRACTION ==========\n"
            "Processing ID : %s\n"
            "Engine Used   : Untouched %s Pipeline\n"
            "Lots Detected : %d Lots\n"
            "===================================",
            processing_id, doc_type, lot_count
        )

    @staticmethod
    def log_stage_common_schema(processing_id: str, lot_index: int, schema: Dict[str, Any]) -> None:
        logger.info(
            "\n========== CANONICAL AI SCHEMA (Lot #%d) ==========\n"
            "auction_number         : %s\n"
            "auction_start_datetime : %s\n"
            "reserve_price          : %s\n"
            "borrower_name          : %s\n"
            "seller_name            : %s\n"
            "asset_location         : %s\n"
            "===================================================",
            lot_index,
            schema.get("auction_number"),
            schema.get("auction_start_datetime"),
            schema.get("reserve_price"),
            schema.get("borrower_name"),
            schema.get("seller_name"),
            schema.get("asset_location"),
        )

    @staticmethod
    def log_stage_ai_validation(processing_id: str, lot_index: int, schema_valid: bool, business_valid: bool, errors: list[str]) -> None:
        logger.info(
            "\n========== AI VALIDATION (Lot #%d) ==========\n"
            "Schema Check   : %s\n"
            "Business Check : %s\n"
            "Errors         : %s\n"
            "=============================================",
            lot_index,
            "PASSED" if schema_valid else "FAILED",
            "PASSED" if business_valid else "FAILED",
            errors if errors else "None"
        )

    @staticmethod
    def log_stage_normalization(processing_id: str, lot_index: int, norm_schema: Dict[str, Any]) -> None:
        logger.info(
            "\n========== NORMALIZATION (Lot #%d) ==========\n"
            "reserve_price          : %s (Cleaned)\n"
            "auction_start_datetime : %s (ISO format)\n"
            "borrower_name          : %s (M/s Legal Restored)\n"
            "=============================================",
            lot_index,
            norm_schema.get("reserve_price"),
            norm_schema.get("auction_start_datetime"),
            norm_schema.get("borrower_name"),
        )

    @staticmethod
    def log_stage_payload_mapping(processing_id: str, lot_index: int, payload: Dict[str, Any]) -> None:
        logger.info(
            "\n========== PAYLOAD MAPPING (Lot #%d) ==========\n"
            "auction_date     <- auction_start_datetime (%s)\n"
            "product_location <- asset_location (%s)\n"
            "reserver_price   <- reserve_price (%s)\n"
            "borrower_name    <- borrower_name (%s)\n"
            "===============================================",
            lot_index,
            payload.get("auction_date"),
            payload.get("product_location"),
            payload.get("reserver_price"),
            payload.get("borrower_name"),
        )

    @staticmethod
    def log_stage_business_defaults(processing_id: str, lot_index: int, payload: Dict[str, Any]) -> None:
        logger.info(
            "\n========== BUSINESS DEFAULTS (Lot #%d) ==========\n"
            "auction_live_status     : %s\n"
            "auction_auto_extension  : %s\n"
            "auto_extension_mode     : %s\n"
            "auction_extend_time_mins: %s\n"
            "currency                : %s\n"
            "================================================",
            lot_index,
            payload.get("auction_live_status"),
            payload.get("auction_auto_extension"),
            payload.get("auto_extension_mode"),
            payload.get("auction_extend_time_mins"),
            payload.get("currency"),
        )

    @staticmethod
    def log_stage_angular_merge(processing_id: str, lot_index: int, payload: Dict[str, Any]) -> None:
        logger.info(
            "\n========== ANGULAR MASTER MERGE (Lot #%d) ==========\n"
            "vendor_id          : %s\n"
            "section_id         : %s\n"
            "part_id            : %s\n"
            "category_id        : %s\n"
            "item_id            : %s\n"
            "auction_image      : %s\n"
            "====================================================",
            lot_index,
            payload.get("vendor_id"),
            payload.get("section_id"),
            payload.get("part_id"),
            payload.get("category_id"),
            payload.get("item_id"),
            payload.get("auction_image"),
        )

    @staticmethod
    def log_stage_consistency_report(processing_id: str, lot_index: int, report: Dict[str, Any]) -> None:
        status = report.get("consistency_status", "UNKNOWN")
        criticals = report.get("critical_errors", 0)
        warns = report.get("warnings", 0)
        logger.info(
            "\n========== END-TO-END CONSISTENCY REPORT (Lot #%d) ==========\n"
            "Processing ID   : %s\n"
            "Status          : %s\n"
            "Critical Errors : %d\n"
            "Warnings        : %d\n"
            "=============================================================",
            lot_index, processing_id, status, criticals, warns
        )

    @staticmethod
    def log_stage_php_validation(processing_id: str, lot_index: int, valid: bool, errors: list[str]) -> None:
        logger.info(
            "\n========== PHP PAYLOAD VALIDATION (Lot #%d) ==========\n"
            "Validation Status : %s\n"
            "Errors            : %s\n"
            "======================================================",
            lot_index,
            "PASSED" if valid else "FAILED",
            errors if errors else "None"
        )

    @staticmethod
    def log_stage_php_result(processing_id: str, lot_index: int, status_code: int, category: str, record_id: str, message: str) -> None:
        logger.info(
            "\n========== PHP INSERT (Lot #%d) ==========\n"
            "HTTP Status : %d\n"
            "Result      : %s\n"
            "PHP ID      : %s\n"
            "Message     : %s\n"
            "==========================================",
            lot_index, status_code, category, record_id or "N/A", message
        )
