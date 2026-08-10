"""
PHP Integration Service.

Stage 9: Dedicated HTTP integration service for sending formatted payloads to the PHP Master Software Insert API.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Tuple
import httpx

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class PHPIntegrationService:
    """
    Handles network communication, HTTP request dispatching, timeouts, retries,
    and response parsing for the PHP Master Software Insert API.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_url = self.settings.php_insert_api_url
        self.timeout = self.settings.php_api_timeout
        self.max_retries = self.settings.php_api_max_retries

    async def insert_auction_record(
        self,
        payload: Dict[str, Any],
        processing_id: str = "N/A",
        lot_index: int = 1,
    ) -> Tuple[bool, str, str, Dict[str, Any]]:
        """
        Send a mapped auction record payload to the PHP Insert API.

        Returns:
            Tuple[success: bool, record_id: str, message: str, raw_response: Dict[str, Any]]
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AuctionAI-Python-Orchestrator/1.0",
        }

        auction_num = payload.get("auction_number", "unknown")
        logger.info(
            "[%s] Sending PHP API Insert Request for Lot #%d (auction_number=%s) to URL: %s",
            processing_id,
            lot_index,
            auction_num,
            self.api_url,
        )

        last_error_msg = ""
        raw_response: Dict[str, Any] = {}

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.post(
                        self.api_url,
                        json=payload,
                        headers=headers,
                    )

                logger.info(
                    "[%s] PHP API HTTP Response: status_code=%d (Attempt %d/%d)",
                    processing_id,
                    response.status_code,
                    attempt,
                    self.max_retries,
                )

                # Parse JSON response body
                try:
                    raw_response = response.json()
                except Exception as json_err:
                    raw_response = {"raw_text": response.text, "json_error": str(json_err)}

                if response.status_code in {200, 201}:
                    # Check internal success keys in PHP response if present
                    # e.g., {"status": true, "message": "Record inserted", "id": "12345"}
                    status_flag = raw_response.get("status") or raw_response.get("success") or True
                    record_id = str(raw_response.get("id") or raw_response.get("auction_id") or raw_response.get("record_id") or "")
                    msg = str(raw_response.get("message") or raw_response.get("msg") or "Record inserted successfully into PHP system.")

                    if status_flag is False or str(status_flag).lower() in {"false", "0", "error", "failed"}:
                        logger.warning(
                            "[%s] PHP API returned HTTP 200 but payload-level failure: %s",
                            processing_id,
                            msg,
                        )
                        return False, record_id, f"PHP Insert Failed: {msg}", raw_response

                    logger.info(
                        "[%s] Successfully inserted record into PHP Master System: record_id=%s, msg=%s",
                        processing_id,
                        record_id,
                        msg,
                    )
                    return True, record_id, msg, raw_response

                else:
                    last_error_msg = f"PHP Server HTTP Error {response.status_code}: {response.text[:200]}"
                    logger.warning("[%s] %s", processing_id, last_error_msg)

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error_msg = f"PHP API Connection/Network Error: {str(net_err)}"
                logger.warning(
                    "[%s] Network error on attempt %d/%d connecting to PHP API: %s",
                    processing_id,
                    attempt,
                    self.max_retries,
                    net_err,
                )
            except Exception as exc:
                last_error_msg = f"Unexpected error during PHP API invocation: {str(exc)}"
                logger.exception("[%s] Unexpected PHP API call exception: %s", processing_id, exc)

            # Retry delay if attempts remaining
            if attempt < self.max_retries:
                await asyncio.sleep(1.0 * attempt)

        # All retries exhausted
        logger.error("[%s] All %d retries failed for PHP API insert: %s", processing_id, self.max_retries, last_error_msg)
        return False, "", last_error_msg, raw_response
