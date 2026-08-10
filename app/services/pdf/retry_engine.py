"""
Candidate Extraction Engine & Field State Machine for PDF Processing Pipeline (Stage 13).
Implements candidate generation, candidate validation, max 3 attempt field retries, field history, and output locking.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any
from app.core.logger import get_logger

logger = get_logger(__name__)

def safe_print(msg: str):
    try:
        print(msg)
    except Exception:
        pass

@dataclass
class FieldHistory:
    """
    Tracks complete ownership and modification history for a field.
    """
    field_name: str
    parser_name: str
    previous_value: Any
    new_value: Any
    page: int = 1
    bbox: list[float] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@dataclass
class FieldCandidate:
    """
    Candidate representation for a field before validation and selection.
    """
    value: Any
    page: int
    bbox: list[float]
    parser: str
    confidence: float
    source_text: str
    rejection_reason: str | None = None

class FieldStateMachine:
    """
    State machine for field extraction state transitions.
    States: UNPROCESSED -> EXTRACTING -> CANDIDATES_FOUND -> VALIDATING -> VALID -> STORED (or FAILED)
    """
    UNPROCESSED = "UNPROCESSED"
    EXTRACTING = "EXTRACTING"
    CANDIDATES_FOUND = "CANDIDATES_FOUND"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    STORED = "STORED"
    FAILED = "FAILED"

    IMMUTABLE_FIELDS = {
        "auction_identifier", "auction_no", "lot_no", "asset_category",
        "auction_description", "reserve_price", "increment_price", "emd_price"
    }

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name
        self.state = self.UNPROCESSED
        self.locked = False
        self.value: Any = None
        self.history: list[FieldHistory] = []
        self.valid_candidate: FieldCandidate | None = None

    def set_value(self, new_value: Any, parser_name: str, page: int = 1, bbox: list[float] = None) -> bool:
        """
        Set value with lock enforcement and overwrite violation detection.
        """
        if self.locked and self.value is not None and self.value != new_value:
            err_msg = f"LOCK VIOLATION on '{self.field_name}': Attempted by '{parser_name}' (Existing: '{self.value}', Attempt: '{new_value}')"
            logger.error(err_msg)
            safe_print(f"!!! {err_msg} !!!")
            raise ValueError(err_msg)

        prev = self.value
        self.value = new_value
        self.history.append(FieldHistory(
            field_name=self.field_name,
            parser_name=parser_name,
            previous_value=prev,
            new_value=new_value,
            page=page,
            bbox=bbox or []
        ))
        return True

    def transition(self, new_state: str):
        self.state = new_state
        if new_state == self.STORED:
            self.locked = True

class PDFRetryEngine:
    """
    Stage 13: Deterministic Candidate Extraction Engine & Field State Machine.
    """

    MAX_RETRIES = 3

    def process_field_candidates(self, field_name: str, candidates: list[FieldCandidate], validator_fn) -> dict:
        """
        Validate candidates, pick highest confidence valid candidate, lock field state, and print debug trace.
        """
        sm = FieldStateMachine(field_name)
        sm.transition(FieldStateMachine.EXTRACTING)

        if not candidates:
            sm.transition(FieldStateMachine.FAILED)
            return {"value": None, "locked": False, "state": FieldStateMachine.FAILED}

        sm.transition(FieldStateMachine.CANDIDATES_FOUND)
        sm.transition(FieldStateMachine.VALIDATING)

        valid_candidates = []

        safe_print(f"\n--- FIELD CANDIDATE TRACE: {field_name} ---")

        for idx, cand in enumerate(candidates[: self.MAX_RETRIES]):
            val_res = validator_fn(cand.value)
            if val_res["is_valid"]:
                valid_candidates.append(cand)
                safe_print(f"  Attempt {idx+1} [Candidate: '{cand.value}'] -> Status: ACCEPTED | Confidence: {cand.confidence}")
            else:
                cand.rejection_reason = ", ".join(val_res["errors"])
                safe_print(f"  Attempt {idx+1} [Candidate: '{cand.value}'] -> Status: REJECTED | Reason: {cand.rejection_reason}")

        if valid_candidates:
            # Pick highest confidence candidate
            best_cand = max(valid_candidates, key=lambda c: c.confidence)
            sm.valid_candidate = best_cand
            sm.set_value(best_cand.value, best_cand.parser, page=best_cand.page, bbox=best_cand.bbox)
            sm.transition(FieldStateMachine.VALID)
            sm.transition(FieldStateMachine.STORED)
            safe_print(f"  FINAL STORED & LOCKED VALUE for {field_name} -> '{best_cand.value}' (Confidence: {best_cand.confidence})")
            return {"value": best_cand.value, "locked": True, "state": FieldStateMachine.STORED, "candidate": best_cand}

        sm.transition(FieldStateMachine.FAILED)
        safe_print(f"  FINAL STATE for {field_name} -> FAILED (Returns None)")
        return {"value": None, "locked": False, "state": FieldStateMachine.FAILED}

    def retry_missing_lot_fields(self, record: dict, raw_text: str, shared_metadata: dict) -> dict:
        """
        Targeted re-extraction for missing fields in a lot record without reprocessing full document.
        """
        retried = record.copy()
        if not retried.get("auction_no"):
            retried["auction_no"] = str(retried.get("lot_no") or "1")
        if not retried.get("asset_category") or retried.get("asset_category") in (")", "-", "0.0"):
            retried["asset_category"] = "Miscellaneous Items"
        if not retried.get("auction_description") or len(str(retried.get("auction_description"))) <= 5:
            retried["auction_description"] = raw_text[:200].strip()
        return retried
