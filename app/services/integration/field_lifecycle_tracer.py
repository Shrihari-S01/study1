"""
Field Lifecycle Tracer & Loss Audit Summary.

Traces mandatory fields from Extraction -> Common AI Schema -> Normalization -> Mapped PHP Payload -> Final API Response.
Outputs clear field lifecycle traces and concise FIELD LOSS SUMMARY tables in backend logs.
"""

from __future__ import annotations

from typing import Any, Dict, NamedTuple
from app.core.logger import get_logger

logger = get_logger(__name__)


class FieldTraceResult(NamedTuple):
    field: str
    severity: str  # 'CRITICAL' | 'IMPORTANT' | 'OPTIONAL'
    extracted_val: str
    common_val: str
    norm_val: str
    mapped_val: str
    status: str  # 'MATCH' | 'RECOVERED' | 'WARNING' | 'CRITICAL_LOSS'
    reason: str  # Explanation of transformation or loss


class FieldLifecycleTracer:
    """
    Deterministic field tracer evaluating field preservation across all pipeline stages.
    """

    TRACE_FIELDS = {
        "auction_number": "CRITICAL",
        "auction_start_datetime": "CRITICAL",
        "auction_end_datetime": "CRITICAL",
        "reserve_price": "CRITICAL",
        "emd_amount": "CRITICAL",
        "borrower_name": "OPTIONAL",
        "seller_name": "CRITICAL",
        "asset_location": "CRITICAL",
        "auction_type": "IMPORTANT",
        "payment_type": "IMPORTANT",
        "event_type": "IMPORTANT",
        "vendor_name": "IMPORTANT",
        "submit_application": "IMPORTANT",
        "first_bid_acceptance_condition": "IMPORTANT",
        "increment_price": "IMPORTANT",
        "remarks": "OPTIONAL",
        "authorized_officer_name": "OPTIONAL",
        "authorized_officer_number": "OPTIONAL",
    }

    @classmethod
    def trace_lifecycle(
        cls,
        raw_extract: Dict[str, Any],
        common_schema: Dict[str, Any],
        norm_schema: Dict[str, Any],
        php_payload: Dict[str, Any],
        lot_index: int = 1,
    ) -> Dict[str, Any]:
        """
        Execute deterministic lifecycle trace across extraction, normalization, mapping, and payload stages.
        """
        results: list[FieldTraceResult] = []
        matched = 0
        recovered = 0
        warnings = 0
        critical_losses = 0

        PHP_KEY_MAP = {
            "reserve_price": "reserver_price",
            "auction_start_datetime": "auction_date",
            "auction_end_datetime": "auction_end_date",
            "seller_name": "institution_seller",
            "asset_location": "product_location",
            "authorized_officer_number": "authorized_officer_no",
            "digital_certificate": "dsc",
        }

        for field_name, severity in cls.TRACE_FIELDS.items():
            php_key = PHP_KEY_MAP.get(field_name, field_name)
            ext_v = str(raw_extract.get(field_name) or raw_extract.get(f"auction_{field_name}") or "").strip()
            com_v = str(common_schema.get(field_name) or "").strip()
            norm_v = str(norm_schema.get(field_name) or "").strip()
            map_v = str(php_payload.get(php_key) or "").strip()

            status = "MATCH"
            reason = "Preserved intact through pipeline"

            if not ext_v and (com_v or map_v):
                status = "RECOVERED"
                reason = "Extracted or inferred in schema builder/mapping stage"
                recovered += 1
            elif ext_v and ext_v.lower() not in {"null", "none", "undefined"} and (not map_v or map_v.lower() in {"null", "none", "0"}):
                if severity == "CRITICAL":
                    status = "CRITICAL_LOSS"
                    reason = f"Extracted '{ext_v}' was cleared/overwritten with '{map_v}' during mapping or validation"
                    critical_losses += 1
                else:
                    status = "WARNING"
                    reason = f"Extracted optional '{ext_v}' was cleared/overwritten with '{map_v}'"
                    warnings += 1
            else:
                matched += 1

            results.append(
                FieldTraceResult(
                    field=field_name,
                    severity=severity,
                    extracted_val=ext_v,
                    common_val=com_v,
                    norm_val=norm_v,
                    mapped_val=map_v,
                    status=status,
                    reason=reason,
                )
            )

        passed = critical_losses == 0

        # Log Field Loss Summary Banner
        logger.info(
            "\n================ FIELD LOSS SUMMARY (Lot #%d) ================\n"
            "Total Fields    : %d\n"
            "Matched         : %d\n"
            "Recovered       : %d\n"
            "Warnings        : %d\n"
            "Critical Losses : %d\n"
            "Status          : %s\n"
            "=============================================================",
            lot_index,
            len(cls.TRACE_FIELDS),
            matched,
            recovered,
            warnings,
            critical_losses,
            "PASSED" if passed else "FAILED",
        )

        return {
            "lot_index": lot_index,
            "status": "PASSED" if passed else "FAILED",
            "matched": matched,
            "recovered": recovered,
            "warnings": warnings,
            "critical_losses": critical_losses,
            "traces": [
                {
                    "field": r.field,
                    "severity": r.severity,
                    "extracted": r.extracted_val,
                    "normalized": r.norm_val,
                    "mapped": r.mapped_val,
                    "status": r.status,
                    "reason": r.reason,
                }
                for r in results
            ],
        }
