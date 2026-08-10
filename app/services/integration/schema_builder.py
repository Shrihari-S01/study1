"""
Common AI Schema Builder.

Stage 2: Standardizes diverse extraction output key names from Image and PDF pipelines
into a single, unified CommonAISchema data structure.
"""

from __future__ import annotations

from typing import Any, Dict
from app.core.logger import get_logger

logger = get_logger(__name__)

class CommonAISchemaBuilder:
    """
    Normalizes pipeline output variations into a consistent Common AI Schema dictionary.
    """

    @staticmethod
    def build_schema(raw_record: Dict[str, Any], lot_index: int = 1) -> Dict[str, Any]:
        """
        Extract and harmonize raw dictionary keys into standardized Common AI Schema.
        Preserves 100% of non-empty extracted values.
        """
        from app.services.extractor.canonical_normalizer import CanonicalAliasNormalizer

        norm_raw = CanonicalAliasNormalizer.normalize_record_aliases(raw_record)

        def get_field(*keys, default: Any = "") -> Any:
            for k in keys:
                if k in norm_raw and norm_raw[k] is not None:
                    val = norm_raw[k]
                    if isinstance(val, (int, float)):
                        if val == 0:
                            continue
                        return val
                    if isinstance(val, str):
                        s = val.strip()
                        if s and s.lower() not in {"null", "none", "n/a", "undefined"}:
                            return s
                    elif val:
                        return val
            return default

        schema: Dict[str, Any] = dict(norm_raw)

        schema.update({
            "lot_index": lot_index,
            "raw_id": get_field("id", "raw_id"),
            "auction_number": get_field("auction_no", "notice_auction_id", "auction_number", "auction_id"),
            "auction_start_datetime": get_field(
                "auction_start_datetime", "auction_start_date_time", "auction_date_time",
                "auction_date", "auction_start_date", "date_of_auction", "date_time_of_auction",
                "auction_schedule", "event_date", "auction_time"
            ),
            "auction_end_datetime": get_field("auction_end_datetime", "auction_end_date_time", "auction_end_date"),
            "reserve_price": get_field(
                "reserve_price", "reserver_price", "reserve_amount", "reserve_rate",
                "starting_price", "auction_start_price", "starting_bid", "opening_bid",
                "upset_price", "base_price", "start_floor_price"
            ),
            "auction_start_price": get_field(
                "auction_start_price", "starting_price", "starting_bid", "opening_bid",
                "upset_price", "base_price", "start_floor_price", "reserve_price"
            ),
            "increment_price": get_field(
                "increment_price", "bid_increment", "bid_increase_amount", "bid_increase",
                "increase_amount", "min_bid_increment", "bid_increment_amount"
            ),
            "emd_amount": get_field(
                "emd_amount", "emd_price", "pre_bid_emd", "emd_value", "deposit_amount"
            ),
            "currency": get_field("currency", default="INR"),
            "borrower_name": get_field("borrower", "borrower_name", "borrower_s", "applicant_name"),
            "seller_name": get_field("institution_seller", "institution_seller_name", "seller_name", "bank_name", "institution"),
            "asset_location": get_field("assets_location", "product_location", "location", "property_address", "address"),
            "asset_type": get_field("asset_type", "asset_category"),
            "asset_category": get_field("asset_category", "asset_subcategory"),
            "description": get_field("auction_description", "auction_details", "description"),
            "auction_type": get_field("auction_type", "event_type"),
            "auto_extension": get_field("auto_extension"),
            "auto_extension_mode": get_field("auto_extension_mode", default="Infinite"),
            "auction_extend_time": get_field("auction_extend_time", "auction_extend_time_mins", default=90),
            "auction_live_status": get_field("auction_live_status", default="Pending"),
            "first_bid_acceptance_condition": get_field("first_bid_acceptance_condition", default="YES"),
            "inspection_from_date": get_field("inspection_from_date", "inspection_schedule_from_date", "inspection_schedule_from"),
            "inspection_to_date": get_field("inspection_to_date", "inspection_schedule_to_date", "inspection_schedule_to"),
            "submit_application": get_field("submit_application", "last_date_of_submission", "last_date_for_submission_of_emd", "emd_submission_date", "last_date_emd", "last_date"),
            "emd_bank_name": get_field("emd_bank_name", "bank_name"),
            "emd_account_no": get_field("emd_account_no", "emd_account_number"),
            "emd_ifsc": get_field("emd_ifsc", "ifsc"),
            "authorized_officer_name": get_field("authorized_officer_name", "authorized_officer", "contact_person"),
            "authorized_officer_number": get_field("authorized_officer_number", "contact_number", "telephone_number"),
            "digital_certificate": get_field("digital_certificate", "dsc"),
            "p_dsc": get_field("p_dsc", "dsc_applicable", "dsc_required"),
            "catalogue_view_date": get_field("catalogue_view_date", "sale_notice_date", "notice_date", "publication_date", "issue_date", "date", "dated", "place_and_date"),
            "full_payment_balance": get_field("full_payment_balance"),
            "delivery_of_material_taken": get_field("delivery_of_material_taken"),
            "quantity": get_field("quantity"),
            "units": get_field("units"),
            "start_floor_price": get_field("start_floor_price"),
            "yard_rent_percent": get_field("yard_rent_percent", "Ground_rent_percent"),
            "remarks": get_field("remarks"),
            # Vehicle fields
            "vehicle_year": get_field("year", "vehicle_year"),
            "vehicle_reg_no": get_field("reg_no", "registration_number", "vehicle_reg_no"),
            "vehicle_rc": get_field("rc", "rc_number", "vehicle_rc"),
            "vehicle_repo_date": get_field("repo_date", "vehicle_repo_date"),
            "vehicle_km_driven": get_field("km_driven", "vehicle_km_driven"),
            "vehicle_chassis_no": get_field("chassis_number", "vehicle_chasis_no"),
            # Gold Carat fields
            "sum_of_carat_18": get_field("sum_of_carat_18"),
            "sum_of_carat_19": get_field("sum_of_carat_19"),
            "sum_of_carat_20": get_field("sum_of_carat_20"),
            "sum_of_carat_21": get_field("sum_of_carat_21"),
            "sum_of_carat_22": get_field("sum_of_carat_22"),
            "sum_of_carat_23": get_field("sum_of_carat_23"),
            "sum_of_carat_24": get_field("sum_of_carat_24"),
            "sum_of_net_weight_total": get_field("sum_of_net_weight_total"),
            "sum_of_gross_weight_total": get_field("sum_of_gross_weight_total"),
        })

        logger.debug("[%d] Built Common AI Schema for auction_number=%s", lot_index, schema["auction_number"])
        return schema


        logger.debug("[%d] Built Common AI Schema for auction_number=%s", lot_index, schema["auction_number"])
        return schema
