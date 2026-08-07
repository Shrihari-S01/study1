"""
Smart PHP API Integration Client.

Stage 9: Manages HTTP POST dispatching to PHP Master Software with granular retry logic & full diagnostic logging:
- ConnectTimeout / ReadTimeout / 5xx Server Error -> Retry with exponential backoff.
- 400 / 422 Client Error / Duplicate Error -> Do NOT retry. Return failure immediately.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Tuple
import httpx

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class PHPIntegrationClient:
    """
    HTTP Client with smart retry policy distinguishing 5xx retriable errors from 4xx non-retriable errors.
    Provides complete diagnostic logging for request payloads, response bodies, headers, and exceptions.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_url = self.settings.php_insert_api_url
        self.timeout = self.settings.php_api_timeout
        self.max_retries = self.settings.php_api_max_retries

    async def send_insert_request(
        self,
        payload: Dict[str, Any],
        processing_id: str = "N/A",
        lot_index: int = 1,
    ) -> Tuple[int, Dict[str, Any], str]:
        """
        Send mapped PHP payload to Master Software Insert API with full diagnostic logging.

        Returns:
            Tuple[http_status_code: int, raw_response_json: Dict[str, Any], error_message: str]
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AuctionAI-Python-Orchestrator/1.0",
        }

        # Requirement 3 & 7: Enforce Schema Validation & Sanitization before sending request
        from app.services.integration.payload_sanitizer import PHPSanitizer
        sanitized_payload, is_valid, schema_errors = PHPSanitizer.sanitize_and_validate_payload(
            payload, processing_id=processing_id
        )

        if not is_valid:
            err_msg = f"Schema Validation Failed before PHP dispatch: {'; '.join(schema_errors)}"
            logger.error("[%s] %s", processing_id, err_msg)
            return 422, {"success": False, "message": err_msg, "errors": schema_errors}, err_msg

        # Audit every payload field for special characters and log complete audit
        special_char_matches = []
        suspicious_chars = ["'", '"', '`', '\\', '\n', '\r', '\t', '\x00']
        
        for k, v in sanitized_payload.items():
            if isinstance(v, str):
                found = [c for c in suspicious_chars if c in v]
                if found:
                    special_char_matches.append((k, v, list(set(found))))
        
        if special_char_matches:
            logger.info(
                "\n==================================================\n"
                "[%s] SPECIAL CHARACTER AUDIT BEFORE DISPATCH\n"
                "Found %d fields containing special/control characters:\n%s\n"
                "==================================================",
                processing_id,
                len(special_char_matches),
                "\n".join(f"  - Field '{field}': Chars {chars} | Value: {val!r}" for field, val, chars in special_char_matches)
            )
        
        post_json_body = json.dumps(sanitized_payload, default=str, ensure_ascii=False)

        auction_num = (
            sanitized_payload.get("p_auction_number")
            or sanitized_payload.get("auction_number")
            or sanitized_payload.get("p_auc_num")
            or sanitized_payload.get("auction_num")
            or "N/A"
        )
        event_type_val = (
            sanitized_payload.get("p_event_type")
            or sanitized_payload.get("event_type")
            or sanitized_payload.get("p_evt_typ")
            or "N/A"
        )

        logger.info(
            "\n========== PHP INSERT API REQUEST (Lot #%d) ==========\n"
            "Processing ID : %s\n"
            "Target URL    : %s\n"
            "HTTP Method   : POST\n"
            "Auction Num   : %s\n"
            "Event Type    : %r (Python Type: %s, JSON Type: %s)\n"
            "Payload Body  : %s\n"
            "=======================================================",
            lot_index,
            processing_id,
            self.api_url,
            auction_num,
            event_type_val,
            type(event_type_val).__name__,
            "number" if isinstance(event_type_val, int) else "string",
            post_json_body,
        )

        last_error = ""
        raw_response: Dict[str, Any] = {}
        status_code = 0

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.post(
                        self.api_url,
                        content=post_json_body,
                        headers=headers,
                    )

                status_code = response.status_code
                resp_text = response.text or ""

                # Try parsing JSON response
                try:
                    raw_response = response.json()
                except Exception as json_err:
                    raw_response = {"raw_text": resp_text, "json_error": str(json_err)}

                logger.info(
                    "\n========== PHP INSERT API RESPONSE (Lot #%d, Attempt %d/%d) ==========\n"
                    "HTTP Status Code : %d\n"
                    "Response Headers : %s\n"
                    "Response Body    : %s\n"
                    "=====================================================================",
                    lot_index,
                    attempt,
                    self.max_retries,
                    status_code,
                    dict(response.headers),
                    resp_text[:1000],
                )

                # 1. Successful HTTP Response (200 / 201)
                if status_code in {200, 201}:
                    return status_code, raw_response, ""

                # 2. Client Errors (400, 422, 409 Duplicate) -> DO NOT RETRY
                elif 400 <= status_code < 500:
                    last_error = f"PHP Client Error HTTP {status_code}: {resp_text[:300]}"
                    logger.warning("[%s] Non-retriable 4xx client error: %s", processing_id, last_error)
                    return status_code, raw_response, last_error

                # 3. Server Errors (500, 502, 503, 504) -> RETRY
                else:
                    last_error = f"PHP Server Error HTTP {status_code}: {resp_text[:300]}"
                    logger.warning("[%s] Retriable 5xx server error on attempt %d/%d: %s", processing_id, attempt, self.max_retries, last_error)

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.NetworkError) as net_err:
                err_type = type(net_err).__name__
                last_error = f"PHP Network Error ({err_type}): {str(net_err)} (Target URL: {self.api_url})"
                logger.warning(
                    "[%s] Retriable network error on attempt %d/%d connecting to PHP API: %s",
                    processing_id,
                    attempt,
                    self.max_retries,
                    last_error,
                )
            except Exception as exc:
                err_type = type(exc).__name__
                last_error = f"Unexpected HTTP Client Exception ({err_type}): {str(exc)}"
                logger.exception("[%s] Unexpected exception on attempt %d/%d: %s", processing_id, attempt, self.max_retries, exc)

            # Exponential backoff retry delay for retriable errors
            if attempt < self.max_retries:
                retry_delay = 1.0 * (2 ** (attempt - 1))
                logger.info("[%s] Waiting %.1fs before retry attempt %d...", processing_id, retry_delay, attempt + 1)
                await asyncio.sleep(retry_delay)

        if not last_error:
            last_error = f"PHP Insert API failed with HTTP {status_code} after {self.max_retries} attempts."

        return status_code or 500, raw_response, last_error
