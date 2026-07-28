"""
Field Mapper.

Maps extracted auction fields
into standardized database fields.
"""

from __future__ import annotations

from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class FieldMapper:
    """
    Maps OCR and LLM extracted fields
    into standardized database fields.
    """

    def __init__(
        self,
    ) -> None:
        """
        Initialize mapper.
        """

        logger.info(
            "Initializing Field Mapper."
        )

        self.mapping = self.build_mapping()


    # ==========================================================
    # Build Mapping
    # ==========================================================

    def build_mapping(
        self,
    ) -> dict:
        """
        Standard field mapping.
        """

        return {

            "bank_name": "bank_name",

            "branch_name": "branch_name",

            "borrower_name": "borrower_name",

            "co_borrower": "co_borrower",

            "guarantor": "guarantor",

            "loan_account_number": "loan_account_number",

            "property_type": "property_type",

            "asset_type": "asset_type",

            "possession_type": "possession_type",

            "property_area": "property_area",

            "reserve_price": "reserve_price",

            "emd_amount": "emd_amount",

            "bid_increment": "bid_increment",

            "auction_date": "auction_date",

            "inspection_date": "inspection_date",

            "demand_notice_date": "demand_notice_date",

            "sale_notice_date": "sale_notice_date",

            "property_address": "property_address",

            "district": "district",

            "state": "state",

            "pin_code": "pin_code",

            "survey_number": "survey_number",

            "door_number": "door_number",

            "village": "village",

            "contact_person": "contact_person",

            "contact_number": "contact_number",

            "email": "email",

            "ifsc": "ifsc",

            "authorized_officer": "authorized_officer",

            "payment_type": "payment_type",

            "are_you_interested": "are_you_interested",

            "institution_seller_name": "institution_seller_name",

            "auction_office_department": "auction_office_department",

            "vendor_name": "vendor_name",

            "authorized_officer_name": "authorized_officer_name",

            "authorized_officer_number": "authorized_officer_number",

            "auction_type": "auction_type",

            "event_type": "event_type",

            "auction_live_status": "auction_live_status",

            "first_bid_acceptance_condition": "first_bid_acceptance_condition",

            "currency": "currency",

            "catalogue_view_date": "catalogue_view_date",

            "auction_start_date_time": "auction_start_date_time",

            "auction_end_date_time": "auction_end_date_time",

            "submit_application": "submit_application",

            "inspection_schedule_from": "inspection_schedule_from",

            "inspection_schedule_to": "inspection_schedule_to",

            "auto_extension": "auto_extension",

            "auto_extension_mode": "auto_extension_mode",

            "auction_extend_time_mins": "auction_extend_time_mins",

            "emd_bank_name": "emd_bank_name",

            "emd_account_no": "emd_account_no",

            "emd_ifsc": "emd_ifsc",

            "digital_certificate": "digital_certificate",

            "remarks": "remarks",

            "auction_no": "auction_no",

            "asset_id": "asset_id",

            "auction_id": "auction_id",

            "asset_category": "asset_category",

            "auction_description": "auction_description",

            "increment_price": "increment_price",

            "dues_amount": "dues_amount",

            "assets_location": "assets_location",

        }

    # ==========================================================
    # Empty Record
    # ==========================================================

    def empty_record(
        self,
    ) -> dict:
        """
        Return empty mapped record.
        """

        return {

            field: ""

            for field

            in self.mapping.values()

        }
    
    # ==========================================================
    # Supported Fields
    # ==========================================================

    def supported_fields(
        self,
    ) -> list[str]:
        """
        Return supported fields.
        """

        return list(

            self.mapping.values()

        )
    
    # ==========================================================
    # Ready Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Service status.
        """

        return True
    

    # ==========================================================
    # Normalize Keys
    # ==========================================================

    def normalize_keys(
        self,
        data: dict,
    ) -> dict:
        """
        Normalize dictionary keys.

        Example:
        Bank Name -> bank_name
        Loan Account Number -> loan_account_number
        """

        normalized = {}

        for key, value in data.items():

            new_key = (

                str(key)

                .strip()

                .lower()

                .replace(" ", "_")

                .replace("-", "_")

            )

            normalized[new_key] = value

        return normalized


    # ==========================================================
    # Alias Mapping
    # ==========================================================

    def alias_mapping(
        self,
    ) -> dict:
        """
        OCR/LLM aliases mapped to
        standard database fields.
        """

        return {

            "bank": "bank_name",

            "bankname": "bank_name",

            "branch": "branch_name",

            "branchname": "branch_name",

            "borrower": "borrower_name",

            "borrowername": "borrower_name",

            "co_applicant": "co_borrower",

            "co_borrower_name": "co_borrower",

            "loan_account": "loan_account_number",

            "loan_account_no": "loan_account_number",

            "loan_no": "loan_account_number",

            "loan_number": "loan_account_number",

            "reserve_amount": "reserve_price",

            "reserveprice": "reserve_price",

            "emd": "emd_amount",

            "auctiondate": "auction_date",

            "inspectiondate": "inspection_date",

            "property": "property_address",

            "address": "property_address",

            "mobile": "contact_number",

            "phone": "contact_number",

            "contact": "contact_number",

            "officer": "authorized_officer",

        }
    

    # ==========================================================
    # Apply Alias
    # ==========================================================

    def apply_alias(
        self,
        data: dict,
    ) -> dict:
        """
        Replace alias names with
        standard field names.
        """

        aliases = self.alias_mapping()

        mapped = {}

        for key, value in data.items():

            key = aliases.get(

                key,

                key,

            )

            mapped[key] = value

        return mapped
    


    # ==========================================================
    # Map Fields
    # ==========================================================

    def map(
        self,
        data: dict,
    ) -> dict:
        """
        Map extracted fields into
        database fields.
        """

        logger.info(
            "Mapping extracted fields."
        )

        mapped = self.empty_record()

        for source, target in self.mapping.items():

            mapped[target] = data.get(

                source,

                "",

            )

        return mapped
    

    # ==========================================================
    # Apply Defaults
    # ==========================================================

    def apply_defaults(
        self,
        data: dict,
    ) -> dict:
        """
        Fill missing fields with
        default values.
        """

        record = self.empty_record()

        for key, value in data.items():

            if key in record:

                record[key] = value

        return record
    

    # ==========================================================
    # Normalize Values
    # ==========================================================

    def normalize_values(
        self,
        data: dict,
    ) -> dict:
        """
        Normalize extracted values.
        """

        normalized = {}

        for key, value in data.items():

            if value is None:

                normalized[key] = ""

                continue

            if isinstance(value, str):

                value = " ".join(

                    value.strip().split()

                )

            normalized[key] = value

        return normalized


    # ==========================================================
    # Process Mapping
    # ==========================================================

    def process(
        self,
        data: dict,
    ) -> dict:
        """
        Complete mapping pipeline.
        """

        logger.info(
            "Processing field mapping."
        )

        data = self.normalize_keys(
            data,
        )

        data = self.apply_alias(
            data,
        )

        data = self.map(
            data,
        )

        data = self.apply_defaults(
            data,
        )

        data = self.normalize_values(
            data,
        )

        return data



    # ==========================================================
    # Merge Records
    # ==========================================================

    def merge(
        self,
        primary: dict,
        secondary: dict,
    ) -> dict:
        """
        Merge two records.

        Primary values override
        secondary values.
        """

        merged = deepcopy(
            secondary,
        )

        for key, value in primary.items():

            if value not in (
                "",
                None,
            ):

                merged[key] = value

        return merged
    

    # ==========================================================
    # Missing Fields
    # ==========================================================

    def missing_fields(
        self,
        data: dict,
    ) -> list[str]:
        """
        Return fields without values.
        """

        missing = []

        for field in self.supported_fields():

            value = data.get(
                field,
                "",
            )

            if value in (
                "",
                None,
            ):

                missing.append(
                    field,
                )

        return missing 
    

    # ==========================================================
    # Available Fields
    # ==========================================================

    def available_fields(
        self,
        data: dict,
    ) -> list[str]:
        """
        Return fields that
        contain values.
        """

        available = []

        for field in self.supported_fields():

            value = data.get(
                field,
                "",
            )

            if value not in (
                "",
                None,
            ):

                available.append(
                    field,
                )

        return available
    

    # ==========================================================
    # Completion Percentage
    # ==========================================================

    def completion_percentage(
        self,
        data: dict,
    ) -> float:
        """
        Calculate mapping completion.
        """

        total = len(
            self.supported_fields(),
        )

        available = len(
            self.available_fields(
                data,
            )
        )

        if total == 0:

            return 0.0

        return round(

            (available / total) * 100,

            2,

        )
    

    # ==========================================================
    # Statistics
    # ==========================================================

    def statistics(
        self,
        data: dict,
    ) -> dict:
        """
        Mapping statistics.
        """

        total = len(
            self.supported_fields(),
        )

        available = len(
            self.available_fields(
                data,
            )
        )

        missing = len(
            self.missing_fields(
                data,
            )
        )

        return {

            "total_fields": total,

            "mapped_fields": available,

            "missing_fields": missing,

            "completion_percentage": self.completion_percentage(
                data,
            ),

        }
    


    # ==========================================================
    # Mapping Score
    # ==========================================================

    def score(
        self,
        data: dict,
    ) -> float:
        """
        Return mapping score
        between 0 and 1.
        """

        return round(

            self.completion_percentage(
                data,
            ) / 100,

            3,

        )
    

    # ==========================================================
    # Validate Mapping
    # ==========================================================

    def validate_mapping(
        self,
        data: dict,
    ) -> bool:
        """
        Verify that all supported fields
        exist in the mapped record.
        """

        required_fields = self.supported_fields()

        return all(

            field in data

            for field in required_fields

        )
    

    # ==========================================================
    # Summary
    # ==========================================================

    def summary(
        self,
        data: dict,
    ) -> dict:
        """
        Return mapping summary.
        """

        return {

            "valid": self.validate_mapping(
                data,
            ),

            "mapped_fields": self.available_fields(
                data,
            ),

            "missing_fields": self.missing_fields(
                data,
            ),

            "statistics": self.statistics(
                data,
            ),

        }

    # ==========================================================
    # Version
    # ==========================================================

    def version(
        self,
    ) -> dict:
        """
        Return mapper information.
        """

        return {

            "service": "Field Mapper",

            "version": "1.0.0",

            "supported_fields": len(

                self.supported_fields(),

            ),

        }
    
    # ==========================================================
    # Reset
    # ==========================================================

    def reset(
        self,
    ) -> dict:
        """
        Reset mapper.
        """

        logger.info(
            "Resetting Field Mapper."
        )

        return self.empty_record()
    
    # ==========================================================
    # Health Check
    # ==========================================================

    def health_check(
        self,
    ) -> dict:
        """
        Return mapper health.
        """

        return {

            "service": "Field Mapper",

            "status": "Healthy",

            "ready": self.is_ready(),

            "supported_fields": len(

                self.supported_fields(),

            ),

        }
    
    # ==========================================================
    # Complete Pipeline
    # ==========================================================

    def pipeline(
        self,
        data: dict,
    ) -> dict:
        """
        Execute complete mapping pipeline.
        """

        logger.info(
            "Starting Field Mapping Pipeline."
        )

        mapped = self.process(
            data,
        )

        return {

            "record": mapped,

            "summary": self.summary(
                mapped,
            ),

            "statistics": self.statistics(
                mapped,
            ),

            "score": self.score(
                mapped,
            ),

        }