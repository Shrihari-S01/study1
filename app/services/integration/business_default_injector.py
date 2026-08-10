"""
Business Default Injector.

Stage 6: Injects business/system default values for fields not extracted from auction notices.
Originates strictly from business rules, NOT extracted document content.
"""

from __future__ import annotations

from typing import Any, Dict
from app.core.logger import get_logger

logger = get_logger(__name__)

class BusinessDefaultInjector:
    """
    Injects business default values into mapped PHP payload.
    """

    @staticmethod
    def inject_defaults(payload: Dict[str, Any], lot_index: int = 1) -> Dict[str, Any]:
        """
        Inject business default rules safely without overwriting existing mapped values.
        """
        res_payload = dict(payload)

        # Business Defaults for Notice Mechanics
        if not res_payload.get("auction_live_status") or str(res_payload.get("auction_live_status")).lower() in {"null", "none", ""}:
            res_payload["auction_live_status"] = "N"

        if not res_payload.get("auction_auto_extension") or str(res_payload.get("auction_auto_extension")).lower() in {"null", "none", ""}:
            res_payload["auction_auto_extension"] = "N"

        if not res_payload.get("auto_extension_mode") or str(res_payload.get("auto_extension_mode")).lower() in {"null", "none", ""}:
            res_payload["auto_extension_mode"] = "Infinite"

        if not res_payload.get("auction_extend_time_mins") or str(res_payload.get("auction_extend_time_mins")).lower() in {"null", "none", ""}:
            res_payload["auction_extend_time_mins"] = 90

        if not res_payload.get("currency") or str(res_payload.get("currency")).lower() in {"null", "none", ""}:
            res_payload["currency"] = "INR"

        logger.debug("[%d] Business Default Injector: Injected business defaults successfully.", lot_index)
        return res_payload
