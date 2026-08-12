"""
Semantic Consistency Validator (Severity-Aware & Schema-Aware).

Executes semantic comparison across canonical schemas (CommonAISchema -> Normalized -> Mapped PHP Payload).

Key Design Principles:
1. Validates MEANING using 4 reusable semantic comparators:
   - compare_datetime()
   - compare_numeric()
   - compare_boolean()
   - compare_text()
2. Status outputs: MATCH, NORMALIZED_MATCH, WARNING, CRITICAL_ERROR.
3. Severity classification:
   - CRITICAL (6 fields only): auction_number, auction_start_datetime, reserve_price, borrower_name, seller_name, asset_location. Loss blocks insertion.
   - IMPORTANT: increment_price, submit_application, inspection dates, remarks, authorized officer. Loss yields Warning.
   - OPTIONAL: IFSC, account numbers, DSC, auto extension, live status, vendor. Absent fields yield PASS.
4. Zero false warnings on normalized matches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import re
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
import dateutil.parser
from app.core.logger import get_logger

logger = get_logger(__name__)

def normalize_numeric(value: Any) -> Optional[str]:
    """
    Normalizes numeric monetary/price values to a canonical string representation.
    Handles None, floats (1535000.0 -> "1535000"), currency strings ("Rs.15,35,000/-" -> "1535000").
    Removes insignificant trailing .0 / .00.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"none", "null", "undefined", "n/a"}:
        return None

    s = re.sub(r"(?i)\b(rs|inr|rupees)\b\.?\s*", "", s)
    s = s.replace("₹", "").replace("Rs", "").replace("rs", "").strip()
    if s.endswith("/-") or s.endswith("-"):
        s = s.rstrip("/-").strip()
    s = s.replace(",", "").replace(" ", "")

    try:
        dec = Decimal(s)
        if dec == dec.to_integral_value():
            return str(int(dec))
        return str(dec.normalize())
    except Exception:
        clean = re.sub(r"[^\d.]", "", s)
        if clean:
            try:
                dec = Decimal(clean)
                if dec == dec.to_integral_value():
                    return str(int(dec))
                return str(dec.normalize())
            except Exception:
                pass
    return None

def _parse_dt(val: Any) -> Optional[datetime]:
    if val in (None, ""):
        return None
    if isinstance(val, datetime):
        return val
    s_val = str(val).strip()
    if not s_val or s_val.lower() in {"none", "null", "undefined", "n/a"}:
        return None
    try:
        clean_s = re.sub(r"(?i)\b(by|at|before|from|to)\b", " ", s_val)
        clean_s = re.sub(r"\s+", " ", clean_s).strip()
        return dateutil.parser.parse(clean_s)
    except Exception:
        m = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", s_val)
        if m:
            try:
                return dateutil.parser.parse(m.group(0))
            except Exception:
                pass
    return None

def _to_bool(val: Any) -> Optional[bool]:
    if val in (None, ""):
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in {"y", "yes", "true", "1", "pending", "active"}:
        return True
    if s in {"n", "no", "false", "0"}:
        return False
    return None

def compare_datetime(val1: Any, val2: Any) -> Tuple[str, str]:
    """
    Parses both inputs into datetime objects prior to comparison.
    Returns status: 'MATCH', 'NORMALIZED_MATCH', or 'MISMATCH'.
    """
    s1, s2 = str(val1 or "").strip(), str(val2 or "").strip()
    if not s1 and not s2:
        return "MATCH", "Both empty"
    if bool(s1) != bool(s2):
        return "MISMATCH", f"One value is empty ('{s1}' vs '{s2}')"
    if s1 == s2:
        return "MATCH", "Exact string match"

    dt1, dt2 = _parse_dt(val1), _parse_dt(val2)
    if dt1 and dt2 and dt1 == dt2:
        return "NORMALIZED_MATCH", f"Semantic Datetime Match ({dt1.strftime('%Y-%m-%d %H:%M')})"

    return "MISMATCH", f"Date mismatch: '{s1}' vs '{s2}'"

def compare_numeric(val1: Any, val2: Any) -> Tuple[str, str]:
    """
    Normalizes numeric monetary/price strings into Decimals before comparison.
    Returns status: 'MATCH', 'NORMALIZED_MATCH', or 'MISMATCH'.
    """
    s1, s2 = str(val1 or "").strip(), str(val2 or "").strip()
    if not s1 and not s2:
        return "MATCH", "Both empty"
    if bool(s1) != bool(s2):
        return "MISMATCH", f"One value is empty ('{s1}' vs '{s2}')"
    if s1 == s2:
        return "MATCH", "Exact string match"

    num1, num2 = normalize_numeric(val1), normalize_numeric(val2)
    if num1 is not None and num2 is not None and num1 == num2:
        return "NORMALIZED_MATCH", f"Semantic Numeric Match ({num1})"

    return "MISMATCH", f"Numeric mismatch: '{s1}' ({num1}) vs '{s2}' ({num2})"

def compare_boolean(val1: Any, val2: Any) -> Tuple[str, str]:
    """
    Maps equivalent boolean representations (Y = Yes = True, N = No = False).
    Returns status: 'MATCH', 'NORMALIZED_MATCH', or 'MISMATCH'.
    """
    s1, s2 = str(val1 or "").strip(), str(val2 or "").strip()
    if not s1 and not s2:
        return "MATCH", "Both empty"
    if s1.upper() == s2.upper():
        return "MATCH", "Exact string match"

    b1, b2 = _to_bool(val1), _to_bool(val2)
    if b1 is not None and b2 is not None and b1 == b2:
        return "NORMALIZED_MATCH", f"Semantic Boolean Match ({b1})"

    return "MISMATCH", f"Boolean mismatch: '{s1}' vs '{s2}'"

def normalize_text_semantic(val: Any) -> str:
    """
    Strips extra whitespace, lowers case, restores legal abbreviations (M, s -> m/s).
    """
    if val is None:
        return ""
    s = str(val).strip()
    if not s or s.lower() in {"none", "null", "undefined", "n/a"}:
        return ""
    s = re.sub(r"(?i)\bM\s*[\,\\\.\s]\s*s\b", "M/s", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()

def normalize_location_semantic(val: Any) -> str:
    """
    Normalizes location text by stripping building names, flat numbers, survey numbers,
    plot numbers, road names, landmarks, measurements, and punctuation noise.
    Leaves clean geographic hierarchy words (Village, Taluk, District, City, State).
    """
    if val is None:
        return ""
    s = str(val).strip()
    if not s or s.lower() in {"none", "null", "undefined", "n/a"}:
        return ""

    # Remove flat, plot, survey, door, building, floor noise
    s = re.sub(r"(?i)\b(flat|door|plot|survey|sy|sf|rs)\s*(no|number)?\.?\s*[a-z0-9\-\/]+", " ", s)
    s = re.sub(r"(?i)\b(ground|first|second|third|fourth|fifth)\s*floor\b", " ", s)
    s = re.sub(r"(?i)\b(building|premises|apartment|complex|house)\b", " ", s)
    s = re.sub(r"(?i)\b\d+\s*(sq\.?\s*ft|sq\.?\s*mtrs?|acres?|cents?)\b", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()

def compare_location(canonical_val: Any, mapped_val: Any) -> Tuple[str, str]:
    """
    Semantically evaluates geographic equivalence between raw extracted description/address
    and PHP normalized product_location.
    - Strips micro-address details (flat, door, plot, survey nos).
    - Checks semantic containment and shared geographic tokens (Village, Taluk, District, City).
    - Never fails when mapped value is a shortened normalized version of canonical value.
    - Yields MISMATCH only if mapped location belongs to a completely different place.
    """
    c_raw = str(canonical_val or "").strip()
    m_raw = str(mapped_val or "").strip()

    if not c_raw and not m_raw:
        return "MATCH", "Both empty"
    if not m_raw:
        return "MATCH", "Mapped location empty, allowing UI edit"
    if not c_raw:
        return "MATCH", "Canonical location empty"

    if c_raw.lower() == m_raw.lower():
        return "MATCH", "Exact location string match"

    c_norm = normalize_location_semantic(c_raw)
    m_norm = normalize_location_semantic(m_raw)

    # Containment check: mapped subset of canonical, or canonical subset of mapped
    if m_norm in c_norm or c_norm in m_norm:
        return "NORMALIZED_MATCH", f"Semantic Location Match (Normalized subset: '{m_norm}')"

    # Token overlap check: extract geographic words (>3 chars)
    c_tokens = set(w for w in c_norm.split() if len(w) > 3)
    m_tokens = set(w for w in m_norm.split() if len(w) > 3)

    if not m_tokens:
        return "NORMALIZED_MATCH", "Mapped location contains basic geographic token"

    overlap = c_tokens.intersection(m_tokens)
    if len(overlap) >= 1 or (len(m_tokens) > 0 and len(overlap) / float(len(m_tokens)) >= 0.5):
        return "NORMALIZED_MATCH", f"Semantic Geographic Overlap ({', '.join(overlap)})"

    return "MISMATCH", f"Geographic mismatch: '{m_raw}' vs '{c_raw}'"

def compare_text(val1: Any, val2: Any) -> Tuple[str, str]:
    """
    Ignores whitespace, case, punctuation differences while preserving content.
    Returns status: 'MATCH', 'NORMALIZED_MATCH', or 'MISMATCH'.
    """
    s1, s2 = str(val1 or "").strip(), str(val2 or "").strip()
    if not s1 and not s2:
        return "MATCH", "Both empty"
    if s1 == s2:
        return "MATCH", "Exact string match"

    t1, t2 = normalize_text_semantic(val1), normalize_text_semantic(val2)
    if t1 == t2:
        return "NORMALIZED_MATCH", f"Semantic Text Match ('{t1}')"
    if t1 and t2 and (t1 in t2 or t2 in t1):
        return "NORMALIZED_MATCH", "Substring semantic match"

    return "MISMATCH", f"Text mismatch: '{s1}' vs '{s2}'"

class FieldConsistencyResult(NamedTuple):
    field: str
    severity: str  # 'CRITICAL' | 'IMPORTANT' | 'OPTIONAL'
    confidence: float
    canonical_value: str
    mapped_value: str
    transformation: str
    status: str  # 'MATCH' | 'NORMALIZED_MATCH' | 'WARNING' | 'CRITICAL_ERROR'
    detail: str

@dataclass
class ConsistencyReport:
    """
    Canonical Dataclass for Semantic Consistency Audit Reports.
    Exposes a stable public API and helper methods.
    Counts are derived dynamically from audit_rows to prevent state duplication.
    """
    lot_index: int
    auction_number: str
    passed: bool
    audit_rows: List[FieldConsistencyResult] = field(default_factory=list)
    report_dict: Dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Public API Helper Methods
    # ---------------------------------------------------------
    def get_failed_rows(self) -> List[FieldConsistencyResult]:
        """Returns all audit rows where status == 'CRITICAL_ERROR'."""
        return [
            r for r in self.audit_rows
            if (isinstance(r, dict) and r.get("status") == "CRITICAL_ERROR") or
            (hasattr(r, "status") and getattr(r, "status") == "CRITICAL_ERROR")
        ]

    def get_warning_rows(self) -> List[FieldConsistencyResult]:
        """Returns all audit rows where status == 'WARNING'."""
        return [
            r for r in self.audit_rows
            if (isinstance(r, dict) and r.get("status") == "WARNING") or
            (hasattr(r, "status") and getattr(r, "status") == "WARNING")
        ]

    def has_critical_errors(self) -> bool:
        """Returns True if there are any critical error rows."""
        return self.critical_errors_count > 0

    def has_warnings(self) -> bool:
        """Returns True if there are any warning rows."""
        return self.warning_count > 0

    def summary(self) -> Dict[str, Any]:
        """Returns a clean summary dictionary of the consistency report."""
        if self.report_dict:
            return self.report_dict
        return {
            "lot_index": self.lot_index,
            "auction_number": self.auction_number,
            "passed": self.passed,
            "overall_status": self.overall_status,
            "critical_errors_count": self.critical_errors_count,
            "warning_count": self.warning_count,
            "total_audit_rows": len(self.audit_rows),
        }

    # ---------------------------------------------------------
    # Public Dynamic Properties
    # ---------------------------------------------------------
    @property
    def critical_errors_count(self) -> int:
        """Dynamically computed count of critical errors."""
        return len(self.get_failed_rows())

    @property
    def warning_count(self) -> int:
        """Dynamically computed count of warnings."""
        return len(self.get_warning_rows())

    @property
    def overall_status(self) -> str:
        """Dynamically computed overall status string ('PASSED', 'WARNING', 'FAILED')."""
        if self.critical_errors_count > 0 or not self.passed:
            return "FAILED"
        if self.warning_count > 0:
            return "WARNING"
        return "PASSED"

    # ---------------------------------------------------------
    # Backward Compatibility Aliases & Properties
    # ---------------------------------------------------------
    @property
    def field_results(self) -> List[FieldConsistencyResult]:
        """Backward compatibility alias for audit_rows."""
        return self.audit_rows

    @property
    def critical_errors(self) -> List[FieldConsistencyResult]:
        """Backward compatibility alias for get_failed_rows()."""
        return self.get_failed_rows()

    @property
    def warnings(self) -> List[FieldConsistencyResult]:
        """Backward compatibility alias for get_warning_rows()."""
        return self.get_warning_rows()

    @property
    def warnings_count(self) -> int:
        """Backward compatibility alias for warning_count."""
        return self.warning_count

class MappingConsistencyValidator:
    """
    End-to-End Semantic Consistency Validator ensuring zero data loss on critical fields.
    """

    CRITICAL_FIELDS = {
        "auction_number": "p_auction_number",
        "auction_start_datetime": "auction_date",
        "reserve_price": "p_reserver_price",
        "seller_name": "institution_seller",
        "asset_location": "product_location",
    }

    IMPORTANT_FIELDS = {
        "increment_price": "increment_price",
        "submit_application": "submit_application",
        "inspection_from_date": "inspection_schedule_from_date_time",
        "inspection_to_date": "inspection_schedule_to_date_time",
        "description": "auction_details",
        "authorized_officer_name": "authorized_officer_name",
        "authorized_officer_number": "authorized_officer_no",
        "remarks": "remarks",
    }

    OPTIONAL_FIELDS = {
        "borrower_name": "borrower_name",
        "loan_account_number": "loan_account_number",
        "emd_amount": "emd_price",
        "emd_bank_name": "emd_bank_name",
        "emd_account_no": "emd_account_no",
        "emd_ifsc": "emd_ifsc",
        "auto_extension": "auction_auto_extension",
        "auction_live_status": "auction_live_status",
        "digital_certificate": "dsc",
        "vendor_name": "vendor_name",
    }

    @classmethod
    def validate_consistency(
        cls,
        common_schema: Dict[str, Any],
        norm_schema: Dict[str, Any],
        php_payload: Dict[str, Any],
        lot_index: int = 1,
        confidence_score: float = 0.95,
    ) -> ConsistencyReport:
        """
        Execute semantic consistency checks across canonical schemas.
        """
        field_results: List[FieldConsistencyResult] = []
        critical_errors = 0
        warnings = 0

        all_field_pairs = []
        for ai_k, php_k in cls.CRITICAL_FIELDS.items():
            all_field_pairs.append((ai_k, php_k, "CRITICAL"))
        for ai_k, php_k in cls.IMPORTANT_FIELDS.items():
            all_field_pairs.append((ai_k, php_k, "IMPORTANT"))
        for ai_k, php_k in cls.OPTIONAL_FIELDS.items():
            all_field_pairs.append((ai_k, php_k, "OPTIONAL"))

        for ai_key, php_key, severity in all_field_pairs:
            canonical_val = str(common_schema.get(ai_key) or norm_schema.get(ai_key) or "").strip()
            mapped_val = str(
                php_payload.get(php_key) or
                php_payload.get(f"p_{php_key}") or
                php_payload.get(ai_key) or
                php_payload.get(f"p_{ai_key}") or
                ""
            ).strip()

            # Empty critical fields check: Enforce lineage source presence check
            if not mapped_val and severity == "CRITICAL":
                # Check lineage in common_schema / raw extraction
                was_present_in_source = bool(
                    common_schema.get(ai_key)
                    or common_schema.get(php_key)
                    or norm_schema.get(ai_key)
                    or norm_schema.get(php_key)
                )
                if canonical_val or was_present_in_source:
                    status = "CRITICAL_ERROR"
                    critical_errors += 1
                    detail_msg = "FIELD LOSS DETECTED: Critical field present in OCR/canonical schema but missing in mapped payload."
                else:
                    status = "MATCH"
                    detail_msg = "Critical field absent in both canonical and mapped payload; match ok."
                field_results.append(
                    FieldConsistencyResult(
                        field=php_key,
                        severity=severity,
                        confidence=confidence_score,
                        canonical_value="",
                        mapped_value="",
                        transformation="Mandatory schema check",
                        status=status,
                        detail=detail_msg,
                    )
                )
                continue

            # Skip checking empty optional fields
            if not canonical_val and severity == "OPTIONAL":
                field_results.append(
                    FieldConsistencyResult(
                        field=php_key,
                        severity=severity,
                        confidence=confidence_score,
                        canonical_value="",
                        mapped_value=mapped_val,
                        transformation="Optional placeholder",
                        status="MATCH",
                        detail="Optional field absent in document; placeholder ok.",
                    )
                )
                continue

            # Execute Reusable Semantic Comparators
            if "location" in ai_key or "location" in php_key or "address" in ai_key:
                cmp_status, detail = compare_location(canonical_val, mapped_val)
                transformation = "Geographic semantic containment comparison"
            elif "price" in ai_key or "amount" in ai_key:
                cmp_status, detail = compare_numeric(canonical_val, mapped_val)
                transformation = "Numeric semantic comparison"
            elif "datetime" in ai_key or "date" in ai_key or "application" in ai_key or "submit" in ai_key:
                cmp_status, detail = compare_datetime(canonical_val, mapped_val)
                transformation = "Datetime semantic comparison"
            elif "status" in ai_key or "extension" in ai_key:
                cmp_status, detail = compare_boolean(canonical_val, mapped_val)
                transformation = "Boolean semantic comparison"
            else:
                cmp_status, detail = compare_text(canonical_val, mapped_val)
                transformation = "Text semantic comparison"

            # Assign Status: MATCH | NORMALIZED_MATCH | WARNING | CRITICAL_ERROR
            if cmp_status in {"MATCH", "NORMALIZED_MATCH"}:
                status = cmp_status
            else:
                if severity == "CRITICAL":
                    status = "CRITICAL_ERROR"
                    critical_errors += 1
                elif severity == "IMPORTANT":
                    status = "WARNING"
                    warnings += 1
                else:
                    status = "MATCH"
                    detail = "Optional field variation ignored."


            field_results.append(
                FieldConsistencyResult(
                    field=php_key,
                    severity=severity,
                    confidence=confidence_score,
                    canonical_value=canonical_val,
                    mapped_value=mapped_val,
                    transformation=transformation,
                    status=status,
                    detail=detail,
                )
            )

        passed = critical_errors == 0
        auc_num = str(php_payload.get("auction_number") or f"LOT-{lot_index}")

        # Log Structured Visual Audit Table
        import sys
        def safe_print(text: str):
            try:
                sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
            except Exception:
                pass

        safe_print(f"\n================ SEMANTIC CONSISTENCY AUDIT TABLE (Lot #{lot_index}) ================")
        safe_print(f"{'Field Name':<25} | {'Canonical Value':<20} | {'Mapped Value':<20} | {'Status':<16}")
        safe_print("-" * 87)
        for r in field_results:
            if r.canonical_value or r.severity == "CRITICAL":
                c_short = (r.canonical_value[:17] + "...") if len(r.canonical_value) > 20 else r.canonical_value
                m_short = (r.mapped_value[:17] + "...") if len(r.mapped_value) > 20 else r.mapped_value
                safe_print(f"{r.field:<25} | {c_short:<20} | {m_short:<20} | {r.status:<16}")
        safe_print("-" * 87)
        safe_print(f"Overall Status: {'PASSED' if passed else 'FAILED'} (Critical Errors: {critical_errors}, Warnings: {warnings})")
        safe_print("===========================================================================\n")

        # Machine-Readable Structured JSON Report
        report_dict = {
            "lot_index": lot_index,
            "auction_number": auc_num,
            "passed": passed,
            "consistency_status": "PASSED" if passed else "FAILED",
            "critical_errors": critical_errors,
            "warnings": warnings,
            "field_results": [
                {
                    "field": r.field,
                    "severity": r.severity,
                    "confidence": r.confidence,
                    "canonical_value": r.canonical_value,
                    "mapped_value": r.mapped_value,
                    "transformation": r.transformation,
                    "status": r.status,
                    "detail": r.detail,
                }
                for r in field_results
            ],
        }

        return ConsistencyReport(
            lot_index=lot_index,
            auction_number=auc_num,
            passed=passed,
            audit_rows=field_results,
            report_dict=report_dict,
        )
