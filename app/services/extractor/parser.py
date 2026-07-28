"""
Auction Parser.

Converts OCR text into structured auction data.
"""

from __future__ import annotations

from copy import deepcopy

from app.core.logger import get_logger

from app.services.extractor.regex import RegexExtractor
from app.services.extractor.validator import Validator
from app.services.extractor.field_mapper import FieldMapper

from app.services.llm.llm_service import LLMService
from app.services.llm.confidence import ConfidenceCalculator

logger = get_logger(__name__)


class AuctionParser:
    """
    Parse OCR text into structured auction fields.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Initializing Auction Parser."
        )

        self.regex = RegexExtractor()

        self.validator = Validator()

        self.mapper = FieldMapper()

        self.llm = LLMService()

        self.confidence = ConfidenceCalculator()

    # ==========================================================
    # Supported Fields
    # ==========================================================

    def supported_fields(
        self,
    ) -> list[str]:
        """
        Return supported auction fields.
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

            "reserve_price",

            "emd_amount",

            "bid_increment",

            "auction_date",

            "inspection_date",

            "property_address",

            "district",

            "state",

            "pin_code",

            "contact_person",

            "contact_number",

            "email",

            "ifsc",

            "authorized_officer",

            # Additional fields extracted by Gemini
            "institution_seller_name",
            "auction_office_department",
            "vendor_name",
            "authorized_officer_name",
            "authorized_officer_number",
            "auction_type",
            "event_type",
            "auction_live_status",
            "first_bid_acceptance_condition",
            "currency",
            "catalogue_view_date",
            "auction_start_date_time",
            "auction_end_date_time",
            "submit_application",
            "inspection_schedule_from",
            "inspection_schedule_to",
            "auto_extension",
            "auto_extension_mode",
            "auction_extend_time_mins",
            "emd_bank_name",
            "emd_account_no",
            "emd_ifsc",
            "payment_type",
            "digital_certificate",
            "are_you_interested",
            "remarks",
            "auction_no",
            "asset_id",
            "auction_id",
            "asset_category",
            "auction_description",
            "property_area",
            "increment_price",
            "dues_amount",
            "assets_location",

        ]

    # ==========================================================
    # Empty Structure
    # ==========================================================

    def empty_record(
        self,
    ) -> dict:
        """
        Return empty auction structure.
        """

        return {

            field: ""

            for field

            in self.supported_fields()

        }
    
    # ==========================================================
    # Reset Record
    # ==========================================================

    def reset(
        self,
    ) -> dict:
        """
        Reset parser.
        """

        return deepcopy(

            self.empty_record()

        )


    # ==========================================================
    # Health Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Check parser dependencies.
        """

        return (

            self.regex.is_ready()

            and

            self.validator.is_ready()

            and

            self.mapper.is_ready()

            and

            self.llm.is_ready()

        )

    
    # ==========================================================
    # Clean OCR Text
    # ==========================================================

    def clean_text(
        self,
        text: str,
    ) -> str:
        """
        Clean OCR output before extraction.
        """

        if not text:

            return ""

        logger.info(
            "Cleaning OCR text."
        )

        text = self.remove_extra_spaces(
            text,
        )

        text = self.remove_special_characters(
            text,
        )

        text = self.normalize_currency(
            text,
        )

        text = self.normalize_dates(
            text,
        )

        text = self.fix_common_ocr_errors(
            text,
        )

        return text.strip()


    # ==========================================================
    # Remove Extra Spaces
    # ==========================================================

    def remove_extra_spaces(
        self,
        text: str,
    ) -> str:
        """
        Remove unnecessary whitespace.
        """

        text = text.replace(
            "\t",
            " ",
        )

        text = text.replace(
            "\r",
            " ",
        )

        while "  " in text:

            text = text.replace(
                "  ",
                " ",
            )

        return text
    

    # ==========================================================
    # Remove Special Characters
    # ==========================================================

    def remove_special_characters(
        self,
        text: str,
    ) -> str:
        """
        Remove unwanted OCR symbols.
        """

        replacements = {

            "|": " ",

            "~": " ",

            "`": " ",

            "•": " ",

            "▪": " ",

            "●": " ",

        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new,
            )

        return text
    


    # ==========================================================
    # Normalize Currency
    # ==========================================================

    def normalize_currency(
        self,
        text: str,
    ) -> str:
        """
        Normalize currency symbols.
        """

        replacements = {

            "Rs .": "Rs.",

            "Rs :": "Rs.",

            "₹ ": "₹",

            "INR ": "Rs.",

        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new,
            )

        return text


    # ==========================================================
    # Normalize Dates
    # ==========================================================

    def normalize_dates(
        self,
        text: str,
    ) -> str:
        """
        Normalize OCR date separators.
        """

        text = text.replace(
            "\\",
            "/",
        )

        text = text.replace(
            "-",
            "/",
        )

        text = text.replace(
            ".",
            "/",
        )

        return text
    

    # ==========================================================
    # Fix Common OCR Errors
    # ==========================================================

    def fix_common_ocr_errors(
        self,
        text: str,
    ) -> str:
        """
        Correct common OCR mistakes.
        """

        corrections = {

            "BANKOF": "BANK OF",

            "RESERVEPRICE": "RESERVE PRICE",

            "AUCTIONDATE": "AUCTION DATE",

            "PROPERTYADDRESS": "PROPERTY ADDRESS",

            "AUTHORISEDOFFICER": "AUTHORISED OFFICER",

            "AUTHORISEDOFFICER": "AUTHORISED OFFICER",

            "EMDAMOUNT": "EMD AMOUNT",

            "ACCOUNTNO": "ACCOUNT NO",

            "LOANACCOUNT": "LOAN ACCOUNT",

            "IFSCCODE": "IFSC CODE",

        }

        upper = text.upper()

        for wrong, correct in corrections.items():

            upper = upper.replace(
                wrong,
                correct,
            )

        return upper


    # ==========================================================
    # Split Text
    # ==========================================================

    def split_lines(
        self,
        text: str,
    ) -> list[str]:
        """
        Split OCR text into lines.
        """

        return [

            line.strip()

            for line in text.split("\n")

            if line.strip()

        ]



    # ==========================================================
    # Remove Empty Lines
    # ==========================================================

    def remove_empty_lines(
        self,
        lines: list[str],
    ) -> list[str]:
        """
        Remove blank lines.
        """

        return [

            line

            for line in lines

            if line

        ]
    

    # ==========================================================
    # Join Lines
    # ==========================================================

    def join_lines(
        self,
        lines: list[str],
    ) -> str:
        """
        Join OCR lines into one text block.
        """

        return "\n".join(lines)
    
    # ==========================================================
    # Preprocess OCR
    # ==========================================================

    def preprocess(
        self,
        text: str,
    ) -> str:
        """
        Complete preprocessing pipeline.
        """

        text = self.clean_text(
            text,
        )

        lines = self.split_lines(
            text,
        )

        lines = self.remove_empty_lines(
            lines,
        )

        return self.join_lines(
            lines,
        )
    
    # ==========================================================
    # Regex Extraction
    # ==========================================================

    def regex_extract(
        self,
        text: str,
        global_text: str = "",
    ) -> dict:
        """
        Extract fields using Regex.
        """

        logger.info(
            "Running Regex Extraction."
        )

        try:

            result = self.regex.extract(
                text,
                global_text=global_text,
            )

            return result

        except Exception:

            logger.exception(
                "Regex extraction failed."
            )

            return self.empty_record()


    # ==========================================================
    # LLM Extraction
    # ==========================================================

    def llm_extract(
        self,
        text: str,
    ) -> dict:
        """
        Extract fields using Gemini LLM.
        """

        logger.info(
            "Running LLM Extraction."
        )

        try:

            result = self.llm.extract(
                text,
            )

            if result is None:

                return self.empty_record()

            return result

        except Exception:

            logger.exception(
                "LLM extraction failed."
            )

            return self.empty_record()


    # ==========================================================
    # Merge Results
    # ==========================================================

    def merge_results(
        self,
        regex_result: dict,
        llm_result: dict,
    ) -> dict:
        """
        Merge Regex and LLM results.

        Regex values are preferred.
        Missing values are filled using LLM.
        """

        logger.info(
            "Merging extraction results."
        )

        merged = self.empty_record()

        for field in self.supported_fields():

            regex_value = regex_result.get(
                field,
                "",
            )

            llm_value = llm_result.get(
                field,
                "",
            )

            if regex_value:

                merged[field] = regex_value

            elif llm_value:

                merged[field] = llm_value

        return merged
    

    # ==========================================================
    # Fill Missing Fields
    # ==========================================================

    def fill_missing(
        self,
        data: dict,
    ) -> dict:
        """
        Replace None values with empty strings.
        """

        for field in self.supported_fields():

            if field not in data:

                data[field] = ""

            if data[field] is None:

                data[field] = ""

        return data



    # ==========================================================
    # Apply Field Mapping
    # ==========================================================

    def map_fields(
        self,
        data: dict,
    ) -> dict:
        """
        Convert extracted fields into
        database field names.
        """

        return self.mapper.map(
            data,
        )
    

    # ==========================================================
    # Confidence
    # ==========================================================

    def calculate_confidence(
        self,
        regex_result: dict,
        llm_result: dict,
        merged_result: dict,
    ) -> dict:
        """
        Calculate confidence for each field.
        """

        logger.info(
            "Calculating confidence."
        )

        return self.confidence.calculate(

            regex_result=regex_result,

            llm_result=llm_result,

            merged_result=merged_result,

        )
    

    # ==========================================================
    # Parse OCR
    # ==========================================================

    def split_ocr_text_into_lots(self, text: str) -> list[str]:
        """
        Split OCR text into individual lot chunks based on lot markers.
        """
        import re
        lines = text.split("\n")
        chunks = []
        current_chunk = []
        
        header_patterns = [
            r"^\s*\d+\s*[\s\.]+\s*(?:M/s|Mr\.|Mrs\.|Borrower|Guarantor)",
            r"DESCRIPTION\s*OF\s*PLANT",
            r"DESCREPTION\s*OF\s*PLANT",
            r"DESCREPTION\s*OF\s*LAND",
            r"DESCRIPTION\s*OF\s*LAND",
            r"DESCREPTION\s*OFLAND",
            r"DESCRIPTION\s*OFLAND",
            r"Property\s*(?:No\.?)?\s*[2-9]",
            r"Lot\s*(?:No\.?)?\s*[2-9]",
        ]
        
        for line in lines:
            is_header = False
            for pattern in header_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    is_guarantor_or_director = any(keyword in line.lower() for keyword in ["director", "guarantor", "w/o", "s/o", "d/o"])
                    is_description_or_boundary = any(keyword in line.lower() for keyword in ["east", "west", "north", "south", "boundary", "boundarles", "adjacent", "khasra", "measuring", "village"])
                    if not is_guarantor_or_director and not is_description_or_boundary:
                        is_header = True
                        break
            
            if is_header and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                
            current_chunk.append(line)
            
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks

    def parse(
        self,
        text: str,
        global_text: str = "",
        raw_text: str = "",
    ) -> dict:
        """
        Parse OCR text into structured data.
        """
        raw_text = raw_text or text

        text = self.preprocess(
            text,
        )

        regex_result = self.regex_extract(
            text,
            global_text=global_text,
        )

        llm_result = self.llm_extract(
            text,
        )

        common = {}
        for group_key in [
            "common_fields",
            "event_and_institution_details",
            "auction_mechanics_and_dates",
            "emd_and_payment_details",
            "portal_specific_fields"
        ]:
            if group_key in llm_result and isinstance(llm_result[group_key], dict):
                common.update(llm_result[group_key])
        
        llm_auctions = llm_result.get("auctions", [])
        if not llm_auctions:
            # Gemini is offline/rate-limited. Run multi-lot regex parser fallback on raw text!
            chunks = self.split_ocr_text_into_lots(raw_text)
            llm_auctions = []
            for chunk in chunks:
                # Skip chunks that do not contain any amount candidates (like header/footer notice text)
                if not self.regex.find_all_amounts(chunk):
                    continue
                chunk_regex = self.regex_extract(chunk, global_text=global_text)
                # Keep common fields from full page (including key aliases)
                for common_field in ["bank_name", "branch_name", "borrower_name", "emd_bank_name", "emd_ifsc", "emd_account_no", "authorized_officer_name", "authorized_officer_number", "contact_number", "ifsc", "authorized_officer", "submit_application", "auction_start_date_time", "auction_end_date_time", "auction_date"]:
                    # Always overwrite header-level notice-wide fields to ensure consistency
                    if common_field in ["bank_name", "branch_name", "borrower_name", "emd_bank_name", "emd_ifsc", "emd_account_no", "authorized_officer_name", "authorized_officer_number"]:
                        if regex_result.get(common_field):
                            chunk_regex[common_field] = regex_result[common_field]
                    elif not chunk_regex.get(common_field):
                        chunk_regex[common_field] = regex_result.get(common_field, "")
                llm_auctions.append(chunk_regex)
            if not llm_auctions:
                llm_auctions = [{}]

        parsed_auctions = []
        confidences = []

        for idx, llm_auc in enumerate(llm_auctions):
            # Construct a flat dictionary for this specific auction
            flat_auc = {}

            # Map common fields and asset specific fields
            for f in self.supported_fields():
                if f in llm_auc and llm_auc[f] not in ("", None):
                    flat_auc[f] = llm_auc[f]
                elif f in common:
                    flat_auc[f] = common[f]
                elif f in llm_auc:
                    flat_auc[f] = llm_auc[f]
                else:
                    flat_auc[f] = ""

            # Merge regex results (safe merge)
            # Only merge target items like reserve_price from regex if empty or 1 auction
            for field in self.supported_fields():
                reg_val = regex_result.get(field, "")
                if reg_val:
                    is_shared = field in [
                        "bank_name", "branch_name", "emd_bank_name",
                        "emd_account_no", "emd_ifsc", "contact_person",
                        "contact_number", "email", "authorized_officer"
                    ]
                    if is_shared or len(llm_auctions) == 1 or not flat_auc.get(field):
                        flat_auc[field] = reg_val

            # Fill missing
            flat_auc = self.fill_missing(flat_auc)

            # Map fields to DB attributes
            mapped_auc = self.map_fields(flat_auc)

            # Create flat representation of LLM results for confidence check
            llm_flat = {}
            for f in self.supported_fields():
                if f in llm_auc and llm_auc[f] not in ("", None):
                    llm_flat[f] = llm_auc[f]
                elif f in common:
                    llm_flat[f] = common[f]
                elif f in llm_auc:
                    llm_flat[f] = llm_auc[f]
                else:
                    llm_flat[f] = ""

            # Calculate confidence score for this item
            conf = self.confidence.calculate(
                regex_result=regex_result,
                llm_result=llm_flat,
                merged_result=mapped_auc,
            )
            mapped_auc["confidence_score"] = conf.get("overall", 0.0)

            parsed_auctions.append(mapped_auc)
            confidences.append(conf)

        return {
            "fields": parsed_auctions,
            "confidence": confidences,
            "regex": regex_result,
            "llm": llm_result,
        }


    # ==========================================================
    # Parse Vision (Direct Scrape)
    # ==========================================================

    def parse_vision(
        self,
        base64_image: str,
        ocr_text: str = "",
        global_ocr_text: str = "",
    ) -> dict:
        """
        Scrape fields directly from image using Vision LLM.
        """
        logger.info(
            "Running direct Vision Extraction."
        )

        try:
            llm_result_str = self.llm.vision_completion(
                base64_image,
                ocr_text=ocr_text
            )
            llm_result = self.llm.parse_json(llm_result_str)
        except Exception as exc:
            logger.error("LLM vision extraction failed: %s.", exc)
            raise RuntimeError(f"Vision extraction failed: {exc}") from exc

        common = {}
        for group_key in [
            "common_fields",
            "event_and_institution_details",
            "auction_mechanics_and_dates",
            "emd_and_payment_details",
            "portal_specific_fields"
        ]:
            if group_key in llm_result and isinstance(llm_result[group_key], dict):
                common.update(llm_result[group_key])

        llm_auctions = llm_result.get("auctions", [])
        if not llm_auctions:
            llm_auctions = [{}]

        parsed_auctions = []
        confidences = []

        for idx, llm_auc in enumerate(llm_auctions):
            # Construct a flat dictionary for this specific auction
            flat_auc = {}

            # Map common fields and asset specific fields
            for f in self.supported_fields():
                if f in llm_auc and llm_auc[f] not in ("", None):
                    flat_auc[f] = llm_auc[f]
                elif f in common:
                    flat_auc[f] = common[f]
                elif f in llm_auc:
                    flat_auc[f] = llm_auc[f]
                else:
                    flat_auc[f] = ""

            # Fill missing
            flat_auc = self.fill_missing(flat_auc)

            # Map fields to DB attributes
            mapped_auc = self.map_fields(flat_auc)

            # Create flat representation of LLM results for confidence check
            llm_flat = {}
            for f in self.supported_fields():
                if f in llm_auc and llm_auc[f] not in ("", None):
                    llm_flat[f] = llm_auc[f]
                elif f in common:
                    llm_flat[f] = common[f]
                elif f in llm_auc:
                    llm_flat[f] = llm_auc[f]
                else:
                    llm_flat[f] = ""

            # Calculate confidence score for this item
            conf = self.confidence.calculate(
                regex_result={},
                llm_result=llm_flat,
                merged_result=mapped_auc,
            )
            mapped_auc["confidence_score"] = conf.get("overall", 0.0)

            parsed_auctions.append(mapped_auc)
            confidences.append(conf)

        return {
            "fields": parsed_auctions,
            "confidence": confidences,
            "regex": {},
            "llm": llm_result,
        }

    
    # ==========================================================
    # Validate Record
    # ==========================================================

    def validate(
        self,
        data: dict,
    ) -> dict:
        """
        Validate extracted fields.
        """

        logger.info(
            "Validating extracted fields."
        )

        try:

            return self.validator.validate(
                data,
            )

        except Exception:

            logger.exception(
                "Validation failed."
            )

            return data


    # ==========================================================
    # Normalize Values
    # ==========================================================

    def normalize(
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

                value = value.strip()

                value = " ".join(
                    value.split(),
                )

            normalized[key] = value

        return normalized



    # ==========================================================
    # Required Fields
    # ==========================================================

    def required_fields(
        self,
    ) -> list[str]:
        """
        Minimum required auction fields.
        """

        return [

            "bank_name",

            "borrower_name",

            "reserve_price",

            "auction_date",

            "property_address",

        ]


    # ==========================================================
    # Missing Fields
    # ==========================================================

    def missing_fields(
        self,
        data: dict,
    ) -> list[str]:
        """
        Find missing fields.
        """

        missing = []

        for field in self.required_fields():

            value = data.get(
                field,
                "",
            )

            if not value:

                missing.append(
                    field,
                )

        return missing 
    

    # ==========================================================
    # Record Completeness
    # ==========================================================

    def completeness(
        self,
        data: dict,
    ) -> float:
        """
        Calculate record completeness.
        """

        total = len(
            self.supported_fields(),
        )

        available = 0

        for field in self.supported_fields():

            if data.get(field):

                available += 1

        return round(

            available / total,

            3,

        )
    

    # ==========================================================
    # Quality Score
    # ==========================================================

    def quality_score(
        self,
        data: dict,
    ) -> float:
        """
        Calculate quality score.
        """

        completeness = self.completeness(
            data,
        )

        missing = len(

            self.missing_fields(
                data,
            )

        )

        score = (

            completeness * 100

        ) - (

            missing * 5

        )

        if score < 0:

            score = 0

        return round(
            score,
            2,
        )
    
    # ==========================================================
    # Validation Summary
    # ==========================================================

    def validation_summary(
        self,
        data: list[dict] | dict,
    ) -> list[dict] | dict:
        """
        Return validation summary.
        """
        if isinstance(data, list):
            return [self.validation_summary(item) for item in data]

        missing = self.missing_fields(
            data,
        )

        return {

            "valid": len(missing) == 0,

            "missing_fields": missing,

            "quality_score": self.quality_score(
                data,
            ),

            "completeness": self.completeness(
                data,
            ),

        }


    # ==========================================================
    # Database Record
    # ==========================================================

    def database_record(
        self,
        data: list[dict] | dict,
    ) -> list[dict] | dict:
        """
        Prepare record for database.
        """
        if isinstance(data, list):
            return [self.database_record(item) for item in data]

        data = self.normalize(
            data,
        )

        data = self.validate(
            data,
        )

        return data
    

    # ==========================================================
    # Process Auction
    # ==========================================================

    def process(
        self,
        ocr_text: str,
    ) -> dict:
        """
        Complete auction parsing pipeline.

        Parameters
        ----------
        ocr_text : str

        Returns
        -------
        dict
        """

        logger.info(
            "Starting auction parser."
        )

        cleaned_text = self.preprocess(
            ocr_text,
        )

        parsed = self.parse(
            cleaned_text,
            raw_text=ocr_text,
        )

        record = self.database_record(
            parsed["fields"],
        )

        validation = self.validation_summary(
            record,
        )

        parsed["record"] = record

        parsed["validation"] = validation

        parsed["statistics"] = self.statistics(
            record,
        )

        logger.info(
            "Auction parser completed."
        )

        return parsed


    # ==========================================================
    # Process Vision (Direct Scrape)
    # ==========================================================

    def process_vision(
        self,
        base64_image: str,
        ocr_text: str = "",
        global_ocr_text: str = "",
    ) -> dict:
        """
        Complete vision auction parsing pipeline.
        """
        logger.info(
            "Starting vision-only scraper."
        )

        parsed = self.parse_vision(
            base64_image,
            ocr_text=ocr_text,
            global_ocr_text=global_ocr_text
        )

        record = self.database_record(
            parsed["fields"],
        )

        validation = self.validation_summary(
            record,
        )

        parsed["record"] = record
        parsed["validation"] = validation
        parsed["statistics"] = self.statistics(
            record,
        )

        logger.info(
            "Vision scraper completed."
        )

        return parsed


    # ==========================================================
    # Batch Process
    # ==========================================================

    def process_batch(
        self,
        texts: list[str],
    ) -> list[dict]:
        """
        Parse multiple auction notices.
        """

        results = []

        logger.info(

            "Processing %d auction notices.",

            len(texts),

        )

        for text in texts:

            try:

                result = self.process(
                    text,
                )

                results.append(
                    result,
                )

            except Exception:

                logger.exception(
                    "Auction parsing failed."
                )

        return results 
    

    # ==========================================================
    # Statistics
    # ==========================================================

    def statistics(
        self,
        record: list[dict] | dict,
    ) -> list[dict] | dict:
        """
        Parser statistics.
        """
        if isinstance(record, list):
            return [self.statistics(item) for item in record]

        total = len(
            self.supported_fields(),
        )

        extracted = sum(

            1

            for value in record.values()

            if value not in [

                "",

                None,

            ]

        )

        return {

            "total_fields": total,

            "extracted_fields": extracted,

            "missing_fields": total - extracted,

            "completion_percentage": round(

                extracted / total * 100,

                2,

            ),

        }
    
    # ==========================================================
    # Health Check
    # ==========================================================

    def health_check(
        self,
    ) -> dict:
        """
        Health check.
        """

        return {

            "service": "Auction Parser",

            "status": "Healthy",

            "regex": self.regex.is_ready(),

            "validator": self.validator.is_ready(),

            "field_mapper": self.mapper.is_ready(),

            "llm": self.llm.is_ready(),

        }

    # ==========================================================
    # Information
    # ==========================================================

    def info(
        self,
    ) -> dict:
        """
        Parser information.
        """

        return {

            "parser": "Auction Parser",

            "version": "1.0.0",

            "supported_fields": len(

                self.supported_fields(),

            ),

            "llm_enabled": True,

            "regex_enabled": True,

        }
    
    # ==========================================================
    # Reset
    # ==========================================================

    def clear(
        self,
    ) -> dict:
        """
        Reset parser.
        """

        logger.info(
            "Parser reset."
        )

        return self.empty_record()
    
    # ==========================================================
    # Close
    # ==========================================================

    def close(
        self,
    ) -> None:
        """
        Close parser services.
        """

        try:

            self.llm.close()

        except Exception:

            pass

        logger.info(
            "Auction Parser closed."
        )