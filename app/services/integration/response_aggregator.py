"""
Response Aggregator.

Stage 9: Aggregates single and multi-lot processing statuses, counts statistics, and builds the final IntegrationResponse object.
Exposes a stable public API preserving backward compatibility and accurate success rules for both Phase 1 and Phase 3.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from app.schemas.integration_schemas import IntegrationResponse, RecordProcessingStatus
from app.core.logger import get_logger

logger = get_logger(__name__)


class ResponseAggregator:
    """
    Aggregates per-lot processing results into consolidated Angular API response.
    """

    @staticmethod
    def build_consolidated_response(
        processing_id: str,
        file_name: str,
        doc_type: str = "PDF",
        elapsed_seconds: float = 0.0,
        record_statuses: Optional[List[RecordProcessingStatus]] = None,
        stage: str = "DOCUMENT_PROCESSED",
        next_action: str = "USER_REVIEW_REQUIRED",
        php_skipped: bool = False,
    ) -> IntegrationResponse:
        """
        Compute total, inserted, failed, validation_failed counts and assemble IntegrationResponse.
        
        Success Rules:
        - Phase 1 (php_skipped=True): success = (validation_failed == 0 and total_records > 0)
        - Phase 3 (php_skipped=False): success = (inserted > 0)
        """
        statuses = record_statuses or []
        total_records = len(statuses)
        inserted = sum(1 for r in statuses if r.php_insert_success)
        validation_failed = sum(1 for r in statuses if not r.validation_success)
        failed = total_records - inserted if not php_skipped else validation_failed

        # Compute granular summary counts
        consistency_failed = 0
        total_warnings = 0
        php_failed = 0

        for r in statuses:
            if r.consistency_report:
                if r.consistency_report.get("passed") is False or r.consistency_report.get("consistency_status") == "FAILED":
                    consistency_failed += 1
                total_warnings += r.consistency_report.get("warnings", 0)
            if not r.php_insert_success and r.validation_success:
                php_failed += 1

        if php_skipped:
            overall_success = (validation_failed == 0 and total_records > 0)
            msg = f"Document '{file_name}' processed successfully ({total_records} records extracted). User review required before submit."
        else:
            overall_success = (inserted > 0)
            if inserted > 0:
                msg = f"Auction submission completed for '{file_name}'. Inserted {inserted}/{total_records} records into PHP Master Software in {elapsed_seconds}s."
            else:
                msg = f"Auction submission failed for '{file_name}'. Inserted 0/{total_records} records into PHP Master Software."

        failed_lots_list = [r.lot_index for r in statuses if not r.php_insert_success]
        summary_counts = {
            "total_records": total_records,
            "total_lots": total_records,
            "inserted": inserted,
            "failed": failed,
            "failed_lots": failed_lots_list,
            "validation_failed": validation_failed,
        }

        proc_summary = {
            "records": total_records,
            "inserted": inserted,
            "consistency_failed": consistency_failed,
            "warnings": total_warnings,
            "php_failed": php_failed if not php_skipped else 0,
        }

        logger.info("[%s] Final Response Aggregated: stage=%s, overall_success=%s, summary=%s", processing_id, stage, overall_success, summary_counts)

        return IntegrationResponse(
            success=overall_success,
            stage=stage,
            next_action=next_action,
            php_skipped=php_skipped,
            processing_id=processing_id,
            file_name=file_name,
            document_type=doc_type,
            processing_time_seconds=elapsed_seconds,
            summary=summary_counts,
            processing_summary=proc_summary,
            records=statuses,
            message=msg,
        )

    @classmethod
    def aggregate_multi_lot_response(
        cls,
        processing_id: str,
        file_name: str,
        file_type: str = "PDF",
        record_statuses: Optional[List[RecordProcessingStatus]] = None,
        total_elapsed_seconds: float = 0.0,
        stage: str = "DOCUMENT_PROCESSED",
        next_action: str = "USER_REVIEW_REQUIRED",
        php_skipped: bool = False,
    ) -> IntegrationResponse:
        """
        Public stable API method for aggregating multi-lot processing statuses.
        """
        return cls.build_consolidated_response(
            processing_id=processing_id,
            file_name=file_name,
            doc_type=file_type,
            elapsed_seconds=total_elapsed_seconds,
            record_statuses=record_statuses,
            stage=stage,
            next_action=next_action,
            php_skipped=php_skipped,
        )

    @staticmethod
    def build_error_response(
        processing_id: str,
        file_name: str,
        doc_type: str = "PDF",
        elapsed_seconds: float = 0.0,
        error_message: str = "Processing failed.",
        stage: str = "ERROR",
    ) -> IntegrationResponse:
        """
        Build unified error response payload.
        """
        return IntegrationResponse(
            success=False,
            stage=stage,
            next_action="RETRY_REQUIRED",
            php_skipped=True,
            processing_id=processing_id,
            file_name=file_name,
            document_type=doc_type,
            processing_time_seconds=elapsed_seconds,
            summary={"total_records": 0, "inserted": 0, "failed": 1, "validation_failed": 1},
            processing_summary={"records": 0, "inserted": 0, "consistency_failed": 0, "warnings": 0, "php_failed": 0},
            records=[],
            message=error_message,
        )
