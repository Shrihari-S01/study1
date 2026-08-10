"""
Angular Master Data Merge Layer.

Stage 7: Merges application inputs received from Angular frontend into mapped PHP payload.
Never compares master IDs or application inputs with OCR or AI extraction.
"""

from __future__ import annotations

import os
from typing import Any, Dict
from app.schemas.integration_schemas import IntegrationMasterData
from app.core.logger import get_logger

logger = get_logger(__name__)

class AngularMasterMerger:
    """
    Merges master IDs and application options received from Angular into PHP payload.
    """

    @staticmethod
    def merge_master_data(
        payload: Dict[str, Any],
        master_data: IntegrationMasterData,
        uploaded_file_path: str = "",
        file_type: str = "IMAGE",
        lot_index: int = 1,
    ) -> Dict[str, Any]:
        """
        Merge Angular master inputs cleanly.
        """
        res = dict(payload)

        res["vendor_id"] = str(master_data.vendor_id or "")
        res["section_id"] = str(master_data.section_id or "")
        res["part_id"] = str(master_data.part_id or "")
        res["category_id"] = str(master_data.category_id or "")
        res["item_id"] = str(master_data.item_id or "")

        res["demo_auction"] = str(master_data.demo_auction or "0")
        res["borrower_required"] = str(master_data.borrower_required or "0")
        res["auction_interested"] = str(master_data.auction_interested or "0")

        # Master overrides for auction_type / payment_type if provided
        if master_data.auction_type and str(master_data.auction_type).strip():
            res["auction_type"] = str(master_data.auction_type).strip()

        if master_data.payment_type and str(master_data.payment_type).strip():
            res["payment_type"] = str(master_data.payment_type).strip()

      
        base_prefix = os.environ.get("FILE_URL_BASE_PREFIX", "http://13.203.147.59:81/auction_sync_india/uploads/")
        generated_file_url = ""
        if uploaded_file_path:
            filename = os.path.basename(uploaded_file_path)
            generated_file_url = f"{base_prefix}{filename}"

        res["auction_image"] = master_data.auction_image_url or (generated_file_url if file_type == "IMAGE" else "")
        res["auction_supporting_docs_1"] = master_data.auction_supporting_docs_1 or (generated_file_url if file_type == "PDF" else "")
        res["auction_supporting_docs_2"] = master_data.auction_supporting_docs_2 or ""

        logger.debug("[%d] Angular Master Merger: Merged Angular inputs successfully.", lot_index)
        return res
