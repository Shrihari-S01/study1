"""
Field Mapping Engine for PDF Auction Processing Pipeline (Stage 10).
Dedicated layer mapping normalized fields to API schema while rejecting invalid assignments.
"""

from app.core.logger import get_logger

logger = get_logger(__name__)

class FieldMapper:
    """
    Stage 10: Dedicated Field Mapping Engine.
    Enforces strict mapping rules:
    - Seller Name cannot populate Auction Number.
    - Category cannot populate Description.
    - Description cannot populate Seller.
    """

    def map_to_schema(self, normalized_record: dict) -> dict:
        """
        Map normalized fields into the standard internal auction record schema.
        """
        mapped = {}

        # 1. Auction Identifier & Number
        mapped["auction_identifier"] = normalized_record.get("auction_identifier")
        raw_auc_no = str(normalized_record.get("auction_no") or normalized_record.get("lot_no") or "").strip()

        # Reject Seller Name assigned as Auction Number
        seller_name = str(normalized_record.get("institution_seller") or "").strip()
        if raw_auc_no and seller_name and raw_auc_no.lower() in seller_name.lower() and len(raw_auc_no) > 10:
            logger.warning("Stage 10 Field Mapper: Rejected Seller Name assigned as auction_no.")
            mapped["auction_no"] = str(normalized_record.get("lot_no") or "")
        else:
            mapped["auction_no"] = raw_auc_no

        # 2. Lot Number & Description
        mapped["lot_no"] = normalized_record.get("lot_no")
        mapped["auction_description"] = normalized_record.get("auction_description")

        # 3. Financial Fields
        mapped["starting_price"] = normalized_record.get("starting_price")
        mapped["reserve_price"] = normalized_record.get("reserve_price") or normalized_record.get("starting_price")
        mapped["increment_price"] = normalized_record.get("increment_price")
        mapped["pre_bid_emd"] = normalized_record.get("pre_bid_emd")
        mapped["emd_price"] = normalized_record.get("emd_price") or normalized_record.get("pre_bid_emd")
        mapped["post_bid_emd_percent"] = normalized_record.get("post_bid_emd_percent")

        # 4. Category & Location
        mapped["asset_category"] = normalized_record.get("asset_category")
        mapped["asset_type"] = normalized_record.get("asset_type") or "Movable"
        mapped["assets_location"] = normalized_record.get("assets_location")

        # 5. Shared Seller & Bank Metadata
        mapped["institution_seller"] = normalized_record.get("institution_seller")
        mapped["auction_office"] = normalized_record.get("auction_office") or normalized_record.get("seller_address")
        mapped["auction_department"] = normalized_record.get("auction_department")
        mapped["emd_bank_name"] = normalized_record.get("emd_bank_name")
        mapped["emd_account_number"] = normalized_record.get("emd_account_number")
        mapped["emd_ifsc"] = normalized_record.get("emd_ifsc")

        # 6. Dates & Timeline
        mapped["catalogue_view_date"] = normalized_record.get("catalogue_view_date")
        mapped["inspection_schedule_from_date"] = normalized_record.get("inspection_schedule_from_date")
        mapped["inspection_schedule_to_date"] = normalized_record.get("inspection_schedule_to_date")
        mapped["auction_date_time"] = normalized_record.get("auction_date_time")
        mapped["auction_end_date_time"] = normalized_record.get("auction_end_date_time")
        mapped["auto_extension"] = normalized_record.get("auto_extension")
        mapped["auction_extend_time"] = normalized_record.get("auction_extend_time")
        mapped["currency"] = normalized_record.get("currency") or "INR"

        return mapped
