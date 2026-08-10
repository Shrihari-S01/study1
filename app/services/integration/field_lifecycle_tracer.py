"""
Field Lifecycle Tracer & Field Loss Logger.

Traces mandatory and optional fields through EVERY pipeline stage:
OCR -> LLM -> parser -> canonical record -> field mapper -> schema builder -> normalizer -> PHP payload -> PHP validator.

If a non-empty value becomes empty/null/"0", logs an explicit warning:
FIELD LOSS DETECTED
field=<name>
record=<lot_index>
previous_value=<prev>
new_value=<new>
stage=<stage_name>
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, NamedTuple, Optional
from app.core.logger import get_logger

logger = get_logger(__name__)

class FieldLossRecord(NamedTuple):
    field: str
    record: int
    previous_value: str
    new_value: str
    stage: str

class FieldLifecycleTracer:
    """
    Field lifecycle protection tracer and field loss logger.
    """

    TRACE_FIELDS = [
        "borrower_name",
        "reserve_price",
        "auction_start_price",
        "emd_amount",
        "emd_price",
        "increment_price",
        "emd_bank_name",
        "emd_account_no",
        "emd_ifsc",
        "auction_number",
        "auction_date",
        "institution_seller",
        "product_location",
        "property_address",
        "auction_details",
    ]

    @classmethod
    def check_and_log_field_loss(
        cls,
        previous_dict: Dict[str, Any],
        current_dict: Dict[str, Any],
        stage_name: str,
        lot_index: int = 1,
    ) -> List[FieldLossRecord]:
        """
        Compares previous_dict vs current_dict for tracked fields.
        If a non-empty value in previous_dict becomes empty/null/"0" in current_dict,
        logs an explicit FIELD LOSS DETECTED alert and returns loss records.
        """
        loss_records: List[FieldLossRecord] = []
        if not previous_dict:
            return loss_records

        PHP_KEY_MAP = {
            "reserve_price": "reserver_price",
            "auction_start_datetime": "auction_date",
            "auction_date": "auction_date",
            "institution_seller": "institution_seller",
            "product_location": "product_location",
            "authorized_officer_number": "authorized_officer_no",
        }

        for field_name in cls.TRACE_FIELDS:
            php_key = PHP_KEY_MAP.get(field_name, field_name)
            prev_v = str(previous_dict.get(field_name) or previous_dict.get(php_key) or "").strip()
            curr_v = str(current_dict.get(field_name) or current_dict.get(php_key) or "").strip()

            is_prev_valid = bool(prev_v) and prev_v.lower() not in {"null", "none", "undefined", "0", "0.0", "0.00"}
            is_curr_invalid = (not curr_v) or curr_v.lower() in {"null", "none", "undefined", "0", "0.0", "0.00"}

            if is_prev_valid and is_curr_invalid:
                loss = FieldLossRecord(
                    field=field_name,
                    record=lot_index,
                    previous_value=prev_v,
                    new_value=curr_v or "EMPTY",
                    stage=stage_name,
                )
                loss_records.append(loss)

                # Explicit MANDATORY Log Format as requested in system specs
                logger.warning(
                    "\n==================================================\n"
                    "FIELD LOSS DETECTED\n"
                    "field=%s\n"
                    "record=%d\n"
                    "previous_value=%r\n"
                    "new_value=%r\n"
                    "stage=%s\n"
                    "==================================================",
                    loss.field,
                    loss.record,
                    loss.previous_value,
                    loss.new_value,
                    loss.stage,
                )

        return loss_records

    @classmethod
    def print_compact_lifecycle_table(
        cls,
        ocr_dict: Dict[str, Any],
        llm_dict: Dict[str, Any],
        parser_dict: Dict[str, Any],
        canonical_dict: Dict[str, Any],
        mapper_dict: Dict[str, Any],
        schema_dict: Dict[str, Any],
        norm_dict: Dict[str, Any],
        php_dict: Dict[str, Any],
        lot_index: int = 1,
    ) -> None:
        """
        Prints compact 12-stage matrix showing field preservation:
        FIELD             OCR   LLM   PARSER   CANONICAL   MAPPER   SCHEMA   NORMALIZER   PHP
        """
        import sys

        def has_val(d: Dict[str, Any], f_name: str) -> str:
            v = str(d.get(f_name) or d.get(f"p_{f_name}") or d.get(f"auction_{f_name}") or "").strip()
            return "YES" if (v and v.lower() not in {"null", "none", "undefined", "0", "0.0", "0.00"}) else "NO"

        rows = []
        first_loss_record = None

        stages = [
            ("OCR", ocr_dict),
            ("LLM", llm_dict),
            ("PARSER", parser_dict),
            ("CANONICAL", canonical_dict),
            ("MAPPER", mapper_dict),
            ("SCHEMA", schema_dict),
            ("NORMALIZER", norm_dict),
            ("PHP", php_dict),
        ]

        for f_name in cls.TRACE_FIELDS:
            pres = [has_val(d, f_name) for _, d in stages]
            rows.append((f_name, pres))

            # Detect FIRST FIELD LOSS
            if first_loss_record is None:
                for i in range(1, len(stages)):
                    prev_stage, prev_d = stages[i-1]
                    curr_stage, curr_d = stages[i]
                    prev_v = str(prev_d.get(f_name) or "").strip()
                    curr_v = str(curr_d.get(f_name) or "").strip()
                    if (prev_v and prev_v.lower() not in {"null", "none", "undefined", "0", "0.0"}) and (not curr_v or curr_v.lower() in {"null", "none", "undefined", "0", "0.0"}):
                        first_loss_record = {
                            "field": f_name,
                            "value_before": prev_v,
                            "value_after": curr_v or "EMPTY",
                            "stage": f"{prev_stage} -> {curr_stage}",
                            "function": f"TransformStage_{curr_stage.lower()}",
                        }
                        break

        # Log compact table
        logger.info("\n================ COMPACT FIELD LIFECYCLE MATRIX (Lot #%d) ================", lot_index)
        logger.info(f"{'FIELD':<20} | {'OCR':<5} | {'LLM':<5} | {'PARSER':<7} | {'CANONICAL':<10} | {'MAPPER':<7} | {'SCHEMA':<7} | {'NORM':<6} | {'PHP':<5}")
        logger.info("-" * 90)
        for f_name, pres in rows:
            logger.info(f"{f_name:<20} | {pres[0]:<5} | {pres[1]:<5} | {pres[2]:<7} | {pres[3]:<10} | {pres[4]:<7} | {pres[5]:<7} | {pres[6]:<6} | {pres[7]:<5}")
        logger.info("=" * 90)

        if first_loss_record:
            logger.warning(
                "\n==================================================\n"
                "FIRST FIELD LOSS:\n"
                "field=%s\n"
                "value_before=%s\n"
                "value_after=%s\n"
                "stage=%s\n"
                "function=%s\n"
                "==================================================",
                first_loss_record["field"],
                first_loss_record["value_before"],
                first_loss_record["value_after"],
                first_loss_record["stage"],
                first_loss_record["function"],
            )
        else:
            logger.info("FIRST FIELD LOSS: NONE (All non-empty fields preserved 100%)")

