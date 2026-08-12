"""
PHP Response Parser.

Stage 8: Parses HTTP response payload from PHP Master Software and categorizes insertion status:
- INSERTED: Successfully inserted into database.
- DUPLICATE: Duplicate auction_number or record already exists.
- VALIDATION_ERROR: PHP payload validation rejected by server.
- DATABASE_ERROR: MySQL/Database insertion failure (e.g. data truncation, constraint violation).
- SERVER_ERROR: Internal server error or connection failure.
"""

from __future__ import annotations

from typing import Any, Dict, NamedTuple, Optional
from app.core.logger import get_logger

logger = get_logger(__name__)

# Keywords indicating MySQL/Database insertion failures even when HTTP code is 200
MYSQL_ERROR_KEYWORDS = [
    "data too long",
    "sqlstate",
    "duplicate entry",
    "integrity constraint",
    "unknown column",
    "cannot add or update child row",
    "foreign key constraint",
    "mysql",
    "syntax error",
    "sql syntax error",
    "column cannot be null",
    "cannot be null",
    "incorrect decimal value",
    "incorrect integer value",
    "incorrect double value",
    "incorrect date",
    "out of range",
    "database error",
    "constraint violation",
    "truncated",
]

class ParsedPHPResponse(NamedTuple):
    success: bool
    status_category: str  # 'INSERTED' | 'DUPLICATE' | 'VALIDATION_ERROR' | 'DATABASE_ERROR' | 'SERVER_ERROR'
    record_id: Optional[str]
    message: str
    raw_payload: Dict[str, Any]

    @property
    def is_success(self) -> bool:
        return self.success

class PHPResponseParser:
    """
    Categorizes raw PHP API HTTP status codes and JSON payloads with strict MySQL error inspection.
    """

    @staticmethod
    def parse_response(
        http_status_code: int,
        raw_json: Dict[str, Any],
        error_detail: str = "",
    ) -> ParsedPHPResponse:
        """
        Analyze HTTP status code and response payload structure for actual database insertion success.
        """
        # Default extraction helpers
        def extract_msg() -> str:
            if isinstance(raw_json, dict):
                return str(raw_json.get("message") or raw_json.get("msg") or raw_json.get("detail") or raw_json.get("error") or "")
            return ""

        def extract_id() -> str:
            if isinstance(raw_json, dict):
                # 1. Top level
                val = raw_json.get("id") or raw_json.get("auction_id") or raw_json.get("record_id") or raw_json.get("insert_id") or raw_json.get("last_insert_id")
                if val:
                    return str(val).strip()
                # 2. Nested under 'data' dict
                data_obj = raw_json.get("data")
                if isinstance(data_obj, dict):
                    d_val = data_obj.get("id") or data_obj.get("auction_id") or data_obj.get("record_id") or data_obj.get("insert_id") or data_obj.get("last_insert_id")
                    if d_val:
                        return str(d_val).strip()
                elif data_obj and not isinstance(data_obj, (dict, list)):
                    d_str = str(data_obj).strip()
                    if d_str.isdigit() or len(d_str) > 0:
                        return d_str
            return ""

        msg = extract_msg() or error_detail or "No message returned by PHP API."
        record_id = extract_id()

        if not record_id:
            logger.info("php_record_id_unavailable = True (PHP API response body does not supply an explicit record ID key)")

        # Construct full response text for keyword checking
        data_field_str = str(raw_json.get("data") or "") if isinstance(raw_json, dict) else ""
        full_text = f"{msg} {data_field_str} {str(raw_json)} {error_detail}".lower()

        # 1. Strict Inspection for MySQL / Database Errors regardless of HTTP status code
        for kw in MYSQL_ERROR_KEYWORDS:
            if kw in full_text:
                db_err_msg = data_field_str if (data_field_str and kw in data_field_str.lower()) else msg
                logger.error("MySQL Insertion Error Detected in PHP API Response: '%s'", db_err_msg)
                return ParsedPHPResponse(
                    success=False,
                    status_category="DATABASE_ERROR",
                    record_id="",
                    message=f"Database Insertion Error: {db_err_msg}",
                    raw_payload=raw_json if isinstance(raw_json, dict) else {"raw": str(raw_json)},
                )

        msg_lower = msg.lower()

        # 2. Successful HTTP Insertion (200 / 201) with clean payload
        if http_status_code in {200, 201}:
            if isinstance(raw_json, dict):
                status_flag = raw_json.get("status")
                success_flag = raw_json.get("success")
                code_flag = raw_json.get("code")

                # If status or success flags explicitly indicate failure/error
                is_explicit_failure = (
                    status_flag is False or
                    success_flag is False or
                    str(status_flag).lower() in {"false", "0", "error", "failed", "failure"} or
                    str(success_flag).lower() in {"false", "0", "error", "failed"} or
                    (code_flag is not None and str(code_flag) not in {"200", "201", "0"})
                )

                if is_explicit_failure:
                    if "duplicate" in msg_lower or "already exist" in msg_lower:
                        return ParsedPHPResponse(
                            success=False,
                            status_category="DUPLICATE",
                            record_id="",
                            message=f"Duplicate Record: {msg}",
                            raw_payload=raw_json,
                        )
                    else:
                        return ParsedPHPResponse(
                            success=False,
                            status_category="VALIDATION_ERROR",
                            record_id="",
                            message=f"PHP Insertion Rejected: {msg}",
                            raw_payload=raw_json,
                        )

            return ParsedPHPResponse(
                success=True,
                status_category="INSERTED",
                record_id=record_id,
                message=msg or "Record inserted successfully into PHP system.",
                raw_payload=raw_json if isinstance(raw_json, dict) else {},
            )

        # 3. Duplicate Detection (409 Conflict or Duplicate message)
        if http_status_code == 409 or "duplicate" in msg_lower or "already exist" in msg_lower:
            return ParsedPHPResponse(
                success=False,
                status_category="DUPLICATE",
                record_id="",
                message=f"Duplicate Record: {msg}",
                raw_payload=raw_json if isinstance(raw_json, dict) else {},
            )

        # 4. Client Validation Errors (400, 422)
        if 400 <= http_status_code < 500:
            return ParsedPHPResponse(
                success=False,
                status_category="VALIDATION_ERROR",
                record_id="",
                message=f"PHP Validation Error: {msg}",
                raw_payload=raw_json if isinstance(raw_json, dict) else {},
            )

        # 5. Server Errors (500, 502, etc.)
        return ParsedPHPResponse(
            success=False,
            status_category="SERVER_ERROR",
            record_id="",
            message=f"PHP Server Error: {msg}",
            raw_payload=raw_json if isinstance(raw_json, dict) else {},
        )
