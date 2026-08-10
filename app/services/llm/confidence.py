"""
Confidence Calculator.

Calculates confidence scores for
auction field extraction.
"""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)

class ConfidenceCalculator:
    """
    Calculate confidence scores for
    extracted auction fields.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Confidence Calculator Initialized."
        )

        self.regex_weight = 0.70

        self.llm_weight = 0.30

    def supported_fields(
        self,
    ) -> list[str]:
        """
        Supported confidence fields.
        """

        return [

            "bank_name",

            "branch_name",

            "borrower_name",

            "co_borrower",

            "guarantor",

            "loan_account_number",

            "property_type",

            "asset_type",

            "possession_type",

            "property_area",

            "reserve_price",

            "emd_amount",

            "bid_increment",

            "auction_date",

            "inspection_date",

            "demand_notice_date",

            "sale_notice_date",

            "property_address",

            "district",

            "state",

            "pin_code",

            "survey_number",

            "door_number",

            "village",

            "contact_person",

            "contact_number",

            "email",

            "ifsc",

            "authorized_officer",

        ]
    

    def empty_record(
        self,
    ) -> dict:
        """
        Empty confidence record.
        """

        return {

            field: 0.0

            for field

            in self.supported_fields()

        }

    def is_ready(
        self,
    ) -> bool:
        """
        Service status.
        """

        return True
    

    def calculate(
        self,
        regex_result: dict,
        llm_result: dict,
        merged_result: dict,
    ) -> dict:
        """
        Calculate confidence for
        every extracted field.
        """

        logger.info(
            "Calculating confidence."
        )

        # Detect if regex results are missing or did not run
        has_regex = any(v for v in regex_result.values() if v not in ["", None])
        if not has_regex:
            self.regex_weight = 0.0
            self.llm_weight = 1.0
        else:
            self.regex_weight = 0.70
            self.llm_weight = 0.30

        confidence = self.empty_record()

        for field in self.supported_fields():

            confidence[field] = self.field_confidence(

                field,

                regex_result,

                llm_result,

                merged_result,

            )

        confidence["overall"] = self.overall(

            confidence,

        )

        return confidence
    

    def field_confidence(
        self,
        field: str,
        regex_result: dict,
        llm_result: dict,
        merged_result: dict,
    ) -> float:
        """
        Calculate confidence for one field.
        """

        regex_value = regex_result.get(
            field,
            "",
        )

        llm_value = llm_result.get(
            field,
            "",
        )

        final_value = merged_result.get(
            field,
            "",
        )

        if not final_value:

            return 0.0

        # If regex did not run or is empty, use the direct LLM confidence score
        has_regex = any(v for v in regex_result.values() if v not in ["", None])
        if not has_regex:
            return self.llm_confidence(llm_value, field)

        regex_score = self.regex_confidence(
            regex_value,
        )

        llm_score = self.llm_confidence(
            llm_value,
            field,
        )

        return self.weighted_confidence(

            regex_score,

            llm_score,

        )
    

    def regex_confidence(
        self,
        value: str,
    ) -> float:
        """
        Confidence from Regex extraction.
        """

        if value in [

            "",

            None,

        ]:

            return 0.0

        return 1.0
    

    def llm_confidence(
        self,
        value: str,
        field: str = None,
    ) -> float:
        """
        Confidence from LLM extraction.
        """

        if value in [

            "",

            None,

        ]:

            return 0.0

        # Base confidence for LLM visual extraction
        score = 0.99

        # Check if the field is numeric and the extracted value is purely numeric
        numeric_fields = ["reserve_price", "emd_amount", "increment_price", "bid_increment"]
        if field in numeric_fields:
            cleaned_val = str(value).replace(",", "").strip()
            if cleaned_val.isdigit() or (cleaned_val.replace(".", "", 1).isdigit() and cleaned_val.count(".") <= 1):
                score = 1.0  # 100% confidence for clean numeric data
            else:
                score = 0.90  # Lower confidence if it contains characters

        # Check if the field is a date and matches standard format YYYY-MM-DD
        date_fields = ["auction_start_datetime", "auction_end_datetime", "inspection_from_date", "inspection_to_date", "submit_application", "auction_date", "inspection_date", "demand_notice_date", "sale_notice_date"]
        if field in date_fields:
            import re
            if re.match(r"^\d{4}-\d{2}-\d{2}", str(value).strip()):
                score = 1.0
            else:
                score = 0.88

        # Check text complexity
        if field == "auction_description" and len(str(value)) > 150:
            score = 0.98

        # Check for standard enumerations
        if field == "asset_type" and str(value).lower() in ["movable", "immovable", "scrap"]:
            score = 1.0
        if field == "possession_type" and any(p in str(value).upper() for p in ["PHYSICAL", "SYMBOLIC", "CONSTRUCTIVE"]):
            score = 1.0

        return score
    

    def weighted_confidence(
        self,
        regex_score: float,
        llm_score: float,
    ) -> float:
        """
        Calculate weighted confidence.
        """

        score = (

            regex_score * self.regex_weight

        ) + (

            llm_score * self.llm_weight

        )

        return round(

            score,

            3,

        )
    

    def confidence_label(
        self,
        score: float,
    ) -> str:
        """
        Convert score into label.
        """

        if score >= 0.90:

            return "Very High"

        if score >= 0.75:

            return "High"

        if score >= 0.50:

            return "Medium"

        if score >= 0.25:

            return "Low"

        return "Very Low"
    

    def available_fields(
        self,
        result: dict,
    ) -> int:
        """
        Count extracted fields.
        """

        return sum(

            1

            for value in result.values()

            if value not in [

                "",

                None,

            ]

        )
    

    def missing_fields(
        self,
        result: dict,
    ) -> int:
        """
        Count missing fields.
        """

        return len(

            self.supported_fields()

        ) - self.available_fields(

            result,

        )

    def summary(
        self,
        confidence: dict,
    ) -> dict:
        """
        Confidence summary.
        """

        overall = confidence.get(

            "overall",

            0.0,

        )

        return {

            "overall_score": overall,

            "label": self.confidence_label(

                overall,

            ),

            "field_count": len(

                self.supported_fields(),

            ),

        }

    def overall(
        self,
        confidence: dict,
    ) -> float:
        """
        Calculate overall confidence score.
        """

        scores = []

        for field in self.supported_fields():

            score = confidence.get(
                field,
                0.0,
            )

            # Average only the fields that were actually populated/extracted
            if score > 0.0:
                scores.append(score)

        if not scores:

            return 0.0

        return round(

            sum(scores) / len(scores),

            3,

        )
    

    def batch_confidence(
        self,
        confidence_list: list[dict],
    ) -> dict:
        """
        Calculate confidence for
        multiple auction notices.
        """

        if not confidence_list:

            return {

                "documents": 0,

                "average_confidence": 0.0,

            }

        overall_scores = [

            item.get(

                "overall",

                0.0,

            )

            for item in confidence_list

        ]

        average = round(

            sum(overall_scores)

            / len(overall_scores),

            3,

        )

        return {

            "documents": len(

                confidence_list,

            ),

            "average_confidence": average,

        }

    def statistics(
        self,
        confidence: dict,
    ) -> dict:
        """
        Confidence statistics.
        """

        overall = confidence.get(

            "overall",

            0.0,

        )

        return {

            "overall": overall,

            "label": self.confidence_label(

                overall,

            ),

            "supported_fields": len(

                self.supported_fields(),

            ),

        }
    

    def version(
        self,
    ) -> dict:
        """
        Service version.
        """

        return {

            "service": "Confidence Calculator",

            "version": "1.0.0",

            "regex_weight": self.regex_weight,

            "llm_weight": self.llm_weight,

        }
    

    def health_check(
        self,
    ) -> dict:
        """
        Service health.
        """

        return {

            "service": "Confidence Calculator",

            "status": "Healthy",

            "ready": self.is_ready(),

        }
    

    def reset(
        self,
    ) -> bool:
        """
        Reset confidence calculator.
        """

        logger.info(
            "Confidence Calculator reset."
        )

        return True 
    

    def process(
        self,
        regex_result: dict,
        llm_result: dict,
        merged_result: dict,
    ) -> dict:
        """
        Complete confidence pipeline.
        """

        logger.info(
            "Starting confidence calculation."
        )

        confidence = self.calculate(

            regex_result,

            llm_result,

            merged_result,

        )

        return {

            "confidence": confidence,

            "summary": self.summary(

                confidence,

            ),

            "statistics": self.statistics(

                confidence,

            ),

        }