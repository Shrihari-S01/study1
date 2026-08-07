"""
Pure Payload Mapper.

Stage 5: Translates Normalized CommonAISchema field names directly into PHP payload keys.
Does NOT inject business defaults (handled by Stage 6 BusinessDefaultInjector).
Does NOT merge Angular master inputs (handled by Stage 7 AngularMasterMerger).
"""

from __future__ import annotations

from typing import Any, Dict
from app.core.logger import get_logger

logger = get_logger(__name__)


class PurePayloadMapper:
    """
    Structural key mapper translating normalized CommonAISchema fields into PHP payload field names.
    """

    @staticmethod
    def extract_borrower_name(data: Dict[str, Any]) -> str:
        """
        Dynamically extract borrower_name from any available borrower source fields:
        borrower_name, borrower, applicant_name, borrower_details, mortgagor_name, guarantor_name, co_borrower.
        Logs source fields found and mapping result.
        """
        b_name = str(data.get("borrower_name") or "").strip()
        b_raw = str(data.get("borrower") or "").strip()
        b_app = str(data.get("applicant_name") or "").strip()
        b_det = str(data.get("borrower_details") or "").strip()
        b_mort = str(data.get("mortgagor_name") or "").strip()
        b_guar = str(data.get("guarantor_name") or "").strip()
        b_cob = str(data.get("co_borrower") or "").strip()

        logger.info(
            "\nBorrower source fields found:\n"
            "  borrower_name    = %r\n"
            "  borrower         = %r\n"
            "  applicant_name   = %r\n"
            "  borrower_details = %r\n"
            "  mortgagor_name   = %r\n"
            "  guarantor_name   = %r\n"
            "  co_borrower      = %r",
            b_name, b_raw, b_app, b_det, b_mort, b_guar, b_cob,
        )

        resolved_borrower = b_name or b_raw or b_app or b_det or b_mort or b_guar or b_cob

        if not resolved_borrower or resolved_borrower.upper() in {"N/A", "NONE", "NULL"}:
            resolved_borrower = ""
        else:
            from app.services.integration.normalizer import DataNormalizer
            clean_b, _ = DataNormalizer.separate_borrower_name_and_address(resolved_borrower)
            if clean_b:
                resolved_borrower = clean_b

        logger.info("Mapping result:\n  borrower_name = %r", resolved_borrower)
        return resolved_borrower

    def map_to_php_payload(
        self,
        norm_schema: Dict[str, Any],
        lot_index: int = 1,
    ) -> Dict[str, Any]:
        """
        Translate normalized CommonAISchema attributes into PHP payload keys.
        """
        from app.services.integration.normalizer import DataNormalizer
        derived_loc = DataNormalizer.derive_product_location(norm_schema)

        payload: Dict[str, Any] = {
            # 1. Identifiers & Location
            "auction_id": str(norm_schema.get("raw_id") or ""),
            "auction_number": str(norm_schema.get("auction_number") or ""),
            "auction_breif": str(norm_schema.get("description") or "")[:100] or "",
            "auction_type": str(norm_schema.get("auction_type") or ""),
            "product_location": derived_loc or str(norm_schema.get("asset_location") or ""),
            "auction_office": str(norm_schema.get("auction_office") or ""),
            "auction_department": str(norm_schema.get("auction_department") or ""),

            # 2. Pricing & Timelines
            "reserver_price": str(norm_schema.get("reserve_price") or ""),
            "auction_start_price": str(norm_schema.get("reserve_price") or ""),
            "increment_price": str(norm_schema.get("increment_price") or ""),
            "emd_price": str(norm_schema.get("emd_amount") or ""),
            "emd_amount": str(norm_schema.get("emd_amount") or ""),

            "auction_date": str(norm_schema.get("auction_start_datetime") or ""),
            "auction_time": str(norm_schema.get("auction_time") or ""),
            "auction_end_date": str(norm_schema.get("auction_end_datetime") or ""),
            "auction_end_time": str(norm_schema.get("auction_end_time") or ""),

            "auction_auto_extension": str(norm_schema.get("auto_extension") or ""),
            "aucto_extension_mode": str(norm_schema.get("auto_extension_mode") or ""),
            "auction_end_time_mins": str(norm_schema.get("auction_extend_time") or ""),
            "auction_details": str(norm_schema.get("description") or ""),

            # 3. Parties & Terms
            "borrower_name": self.extract_borrower_name(norm_schema),
            "institution_seller": str(norm_schema.get("seller_name") or ""),
            "vendor_name": str(norm_schema.get("seller_name") or norm_schema.get("vendor_name") or ""),
            "event_type": str(norm_schema.get("auction_type") or ""),
            "first_bid_acceptance_condition": str(norm_schema.get("first_bid_acceptance_condition") or ""),
            "digital_certificate": str(norm_schema.get("digital_certificate") or ""),
            "dsc": str(norm_schema.get("digital_certificate") or ""),
            "p_dsc": str(norm_schema.get("p_dsc") or norm_schema.get("dsc_applicable") or norm_schema.get("dsc") or norm_schema.get("digital_certificate") or ""),
            "catalogue_view_date": str(norm_schema.get("catalogue_view_date") or ""),
            "inspection_schedule_from_date_time": str(norm_schema.get("inspection_from_date") or ""),
            "inspection_schedule_to_date_time": str(norm_schema.get("inspection_to_date") or ""),
            "currency": str(norm_schema.get("currency") or ""),
            "submit_application": str(norm_schema.get("submit_application") or ""),
            "remarks": str(norm_schema.get("remarks") or ""),

            # 4. Vehicle Specific Fields
            "vehicle_year": str(norm_schema.get("vehicle_year") or ""),
            "vehicle_reg_no": str(norm_schema.get("vehicle_reg_no") or ""),
            "vehicle_rc": str(norm_schema.get("vehicle_rc") or ""),
            "vehicle_repo_date": str(norm_schema.get("vehicle_repo_date") or ""),
            "vehicle_km_driven": str(norm_schema.get("vehicle_km_driven") or ""),
            "vehicle_chasis_no": str(norm_schema.get("vehicle_chassis_no") or ""),

            # 5. Scrap & Gold Carat Fields
            "scrap_qty": str(norm_schema.get("quantity") or ""),
            "scrap_uom": str(norm_schema.get("units") or ""),
            "scarp_start_floor_price": str(norm_schema.get("start_floor_price") or ""),
            "sum_of_18_carat": str(norm_schema.get("sum_of_carat_18") or ""),
            "sum_of_19_carat": str(norm_schema.get("sum_of_carat_19") or ""),
            "sum_of_20_carat": str(norm_schema.get("sum_of_carat_20") or ""),
            "sum_of_21_carat": str(norm_schema.get("sum_of_carat_21") or ""),
            "sum_of_22_carat": str(norm_schema.get("sum_of_carat_22") or ""),
            "sum_of_23_carat": str(norm_schema.get("sum_of_carat_23") or ""),
            "sum_of_24_carat": str(norm_schema.get("sum_of_carat_24") or ""),
            "sum_of_net_total_wt": str(norm_schema.get("sum_of_net_weight_total") or ""),
            "sum_of_gross_total_wt": str(norm_schema.get("sum_of_gross_weight_total") or ""),

            # 6. EMD Bank & Officer Details
            "emd_bank_name": str(norm_schema.get("emd_bank_name") or ""),
            "emd_account_no": str(norm_schema.get("emd_account_no") or ""),
            "emd_ifsc": str(norm_schema.get("emd_ifsc") or ""),
            "authorized_officer_no": str(norm_schema.get("authorized_officer_number") or ""),
            "authorized_officer_name": str(norm_schema.get("authorized_officer_name") or ""),
        }

        logger.debug("[%d] Pure Payload Mapper: Translated CommonAISchema fields to PHP payload keys.", lot_index)
        return payload
