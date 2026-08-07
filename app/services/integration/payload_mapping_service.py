"""
Payload Mapping Service.

Stage 6, 7 & 8: Maps extracted AI schema dictionary + Angular master values into the exact 74-field PHP payload schema.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.core.logger import get_logger
from app.schemas.integration_schemas import IntegrationMasterData

logger = get_logger(__name__)


class PayloadMappingService:
    """
    Dedicated mapping service responsible for transforming AI extraction outputs
    and system master values into the exact PHP Master Software payload structure.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def build_php_payload(
        self,
        extracted_record: Dict[str, Any],
        master_data: IntegrationMasterData,
        uploaded_file_path: Optional[str] = None,
        file_type: str = "PDF",
    ) -> Dict[str, str]:
        """
        Construct the complete 74-field JSON payload expected by the PHP Insert API.
        """

        # Helper to safely extract string values
        def s(key: str, default: str = "") -> str:
            val = extracted_record.get(key)
            if val is None or str(val).strip().lower() in {"none", "undefined", "null"}:
                return default
            return str(val).strip()

        # Helper to format numeric values to clean string
        def num_str(key: str, default: str = "") -> str:
            raw = s(key)
            if not raw:
                return default
            clean = re.sub(r"[^\d.]", "", raw)
            if clean:
                try:
                    # Return formatted float string or integer string
                    flt = float(clean)
                    return f"{int(flt)}" if flt.is_integer() else f"{flt:.2f}"
                except ValueError:
                    pass
            return default

        # Helper to format datetimes to ISO "YYYY-MM-DDTHH:MM" format
        def dt_str(key: str, default: str = "") -> str:
            val = extracted_record.get(key)
            if not val:
                return default
            if isinstance(val, (datetime,)):
                return val.strftime("%Y-%m-%dT%H:%M")
            val_str = str(val).strip()
            # Try parsing ISO strings
            try:
                dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%dT%H:%M")
            except Exception:
                pass
            return val_str

        # File URL Handling (Stage 8)
        base_prefix = self.settings.file_url_base_prefix.rstrip("/") + "/"
        generated_file_url = ""
        if uploaded_file_path:
            filename = os.path.basename(uploaded_file_path)
            generated_file_url = f"{base_prefix}{filename}"

        img_url = master_data.auction_image_url or (generated_file_url if file_type == "IMAGE" else "")
        doc1_url = master_data.auction_supporting_docs_1 or (generated_file_url if file_type == "PDF" else "")
        doc2_url = master_data.auction_supporting_docs_2 or ""

        # Flag mapping helpers
        def flag(val: str, default: str = "N") -> str:
            if not val:
                return default
            v = val.strip().lower()
            if v in {"yes", "true", "1", "y"}:
                return "Y"
            if v in {"no", "false", "0", "n"}:
                return "N"
            return default

        auto_ext_flag = flag(s("auto_extension"), default="N")
        live_status = s("auction_live_status", "N")
        if live_status.lower() in {"pending", "active", "y", "true"}:
            live_status_flag = "Y"
        else:
            live_status_flag = "N"

        # Build complete 74-field dictionary matching exact PHP payload specification
        payload: Dict[str, str] = {
            # 1. Identifiers & General Details
            "auction_id": s("id", ""),
            "auction_number": s("auction_no") or s("notice_auction_id") or s("auction_number", ""),
            "auction_breif": s("auction_description")[:100] if s("auction_description") else "null",
            "auction_type": master_data.auction_type or s("auction_type", "2"),
            "product_location": s("assets_location") or s("location", ""),
            "auction_office": s("auction_office", ""),

            # 2. Pricing & Extensions
            "reserver_price": num_str("auction_start_price") or num_str("reserve_price", ""),
            "increment_price": num_str("increment_price", ""),
            "auction_date": dt_str("auction_start_datetime") or dt_str("auction_date", ""),
            "auction_time": s("auction_time", ""),
            "auction_end_date": dt_str("auction_end_datetime") or dt_str("auction_end_date", ""),
            "auction_end_time": s("auction_end_time", ""),
            "auction_auto_extension": auto_ext_flag,
            "aucto_extension_mode": s("auto_extension_mode", "Infinite"),
            "auction_end_time_mins": str(extracted_record.get("auction_extend_time", "90")),
            "auction_details": s("auction_description", ""),

            # 3. Documents & System Master Fields from Angular
            "auction_image_url": img_url,
            "auction_supporting_docs_1": doc1_url,
            "auction_supporting_docs_2": doc2_url,
            "section_id": master_data.section_id,
            "part_id": master_data.part_id,
            "category_id": master_data.category_id or s("asset_category", ""),
            "item_id": master_data.item_id,
            "demo_auction": master_data.demo_auction,
            "borrower_name": s("borrower", "null"),
            "institution_seller": s("institution_seller") or s("seller") or s("vendor_name", ""),
            "auction_active_status": s("auction_active_status", ""),
            "auction_live_status": live_status_flag,
            "emd_price": num_str("emd_amount") or num_str("emd_price", ""),
            "emd_required": flag(s("emd_required"), default="Y" if num_str("emd_amount") else ""),
            "auction_department": s("auction_department", ""),
            "event_type": s("event_type", ""),
            "auction_start_price": num_str("auction_start_price") or num_str("reserve_price", ""),
            "first_bid_acceptance_condition": s("first_bid_acceptance_condition", "YES"),
            "digital_certificate": s("digital_certificate", ""),
            "dsc": s("dsc") or s("digital_certificate", ""),
            "p_dsc": s("p_dsc") or s("dsc_applicable") or s("dsc") or s("digital_certificate", ""),
            "catalogue_view_date": s("catalogue_view_date", ""),
            "inspection_schedule_from_date_time": dt_str("inspection_from_date") or dt_str("inspection_schedule_from_date_time", ""),
            "inspection_schedule_to_date_time": dt_str("inspection_to_date") or dt_str("inspection_schedule_to_date_time", ""),
            "currency": s("currency", "INR"),
            "post_bid_emd_to_deposit": s("post_bid_emd_to_deposit", ""),
            "full_payment_balance_payment_deposited": num_str("full_payment_balance", ""),
            "delivery_of_the_material_to_be_taken": s("delivery_of_material_taken", ""),
            "Ground_rent_percent": s("yard_rent_percent", ""),
            "submit_application": s("submit_application", "None"),
            "remarks": s("remarks", "null"),

            # 4. Vehicle Specific Fields
            "vehicle_year": s("year", ""),
            "vehicle_reg_no": s("reg_no", ""),
            "vehicle_rc": s("rc", ""),
            "vehicle_repo_date": s("repo_date", ""),
            "vehicle_km_driven": s("km_driven", ""),
            "vehicle_chasis_no": s("chassis_number", ""),

            # 5. Scrap & Gold Carat Fields
            "scrap_qty": s("quantity", ""),
            "scrap_uom": s("units", ""),
            "scarp_start_floor_price": num_str("start_floor_price", ""),
            "sum_of_18_carat": flag(s("sum_of_carat_18"), default="N"),
            "sum_of_19_carat": flag(s("sum_of_carat_19"), default="N"),
            "sum_of_20_carat": flag(s("sum_of_carat_20"), default="N"),
            "sum_of_21_carat": flag(s("sum_of_carat_21"), default="N"),
            "sum_of_22_carat": flag(s("sum_of_carat_22"), default="N"),
            "sum_of_23_carat": flag(s("sum_of_carat_23"), default="N"),
            "sum_of_24_carat": flag(s("sum_of_carat_24"), default="N"),
            "sum_of_net_total_wt": s("sum_of_net_weight_total", ""),
            "sum_of_gross_total_wt": s("sum_of_gross_weight_total", ""),

            # 6. EMD Bank & Officer Details
            "emd_bank_name": s("emd_bank_name", "null"),
            "emd_account_no": s("emd_account_no", ""),
            "emd_ifsc": s("emd_ifsc", "null"),
            "emd_amount": num_str("emd_amount", ""),
            "authorized_officer_no": s("authorized_officer_number", "null"),
            "authorized_officer_name": s("authorized_officer_name", "null"),

            # 7. Additional Angular System Values
            "vendor_id": master_data.vendor_id,
            "payment_type": master_data.payment_type or s("payment_type", "AMOUNT"),
            "borrower_required": master_data.borrower_required,
            "auction_interested": master_data.auction_interested,
        }

        logger.debug("Successfully mapped extraction record into PHP payload: auction_number=%s", payload["auction_number"])
        return payload
