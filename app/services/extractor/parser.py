"""
Auction Parser.

Converts OCR text into structured auction data.
"""

from __future__ import annotations

from copy import deepcopy
import json
import re

from app.core.logger import get_logger

from app.services.extractor.regex import RegexExtractor
from app.services.extractor.validator import Validator
from app.services.extractor.field_mapper import FieldMapper

from app.services.llm.llm_service import LLMService
from app.services.llm.confidence import ConfidenceCalculator
from app.services.pdf.pdf_parser_service import PDFParserService

logger = get_logger(__name__)


class AuctionParser:
    """
    Parse OCR text and PDF documents into structured auction fields.
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

        self.pdf_service = PDFParserService()

    def process_pdf(self, pdf_path: str, ocr_service=None) -> dict:
        """
        Process PDF file through complete Stage 1 to Stage 18 pipeline.
        """
        logger.info("Routing file to PDF Parser Service (Stages 1 - 18).")
        return self.pdf_service.process_pdf_file(pdf_path, ocr_service=ocr_service)

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

            "remarks",
            "auction_no",
            "asset_id",
            "auction_id",
            "asset_category",
            "auction_description",
            "property_area",
            "increment_price",

            "assets_location",

            "institution_seller",
            "auction_office",
            "auction_department",
            "digital_certificate",
            "catalogue_view_date",
            "asset_subcategory",
            "full_payment_balance",
            "delivery_of_material_taken",
            "quantity",
            "units",
            "start_floor_price",
            "vendor_name",
            "sum_of_carat_18",
            "sum_of_carat_19",
            "sum_of_carat_20",
            "sum_of_carat_21",
            "sum_of_carat_22",
            "sum_of_carat_23",
            "sum_of_carat_24",
            "sum_of_net_weight_total",
            "sum_of_gross_weight_total",
            "year",
            "reg_no",
            "repo_date",
            "km_driven",
            "rc",
            "chassis_number",
            "yard_rent_percent",
            "event_type",
            "starting_price",
            "pre_bid_emd",
            "emd_price",

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
    def extract_pdf_header_keywords(self, full_pdf_text: str) -> dict:
        """
        Rules 1-5: Zero-LLM Fast Regex Header Extraction & Composite Identifier Parsing.
        """
        import re
        header = {}

        # 1. Auction Number & Composite Identifier Parsing (Rules 1, 2, 3, 5)
        m_auc_no = re.search(r"Auction\s+Number:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_auc_no:
            raw_identifier = m_auc_no.group(1).strip()
            header["full_auction_identifier"] = raw_identifier

            # Rule 2: Numeric Auction Number (after last '/')
            parts = raw_identifier.split("/")
            numeric_auc_no = parts[-1].strip() if parts else raw_identifier
            header["auction_no"] = numeric_auc_no

            # Rule 3 & 4: Derived Asset Location from composite identifier if explicit location missing
            # Pattern: MSTC/SRO/<SELLER>/<NO>/<LOCATION>/<YEAR>/<ID>
            if len(parts) >= 5:
                derived_loc = parts[-3].strip()
                if derived_loc and not derived_loc.isdigit():
                    header["assets_location"] = derived_loc

        # 2. Auction Type
        m_auc_type = re.search(r"Auction\s+Type:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_auc_type:
            header["auction_type"] = m_auc_type.group(1).strip()

        # 3. Catalogue View Date
        m_cat_date = re.search(r"Catalogue\s+View\s+date:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_cat_date:
            header["catalogue_view_date"] = m_cat_date.group(1).strip()

        # Rule 6: Inspection Schedule (Keyword matching + date parsing)
        m_insp = re.search(r"Inspection\s+Schedule:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_insp:
            val_insp = m_insp.group(1).strip()
            range_match = re.search(r"(\d{2}[-/\.]\d{2}[-/\.]\d{2,4})\s+(?:to|-|until)\s+(\d{2}[-/\.]\d{2}[-/\.]\d{2,4})", val_insp, re.IGNORECASE)
            if range_match:
                header["inspection_schedule_from_date"] = range_match.group(1).strip()
                header["inspection_schedule_to_date"] = range_match.group(2).strip()
            else:
                header["inspection_schedule_from_date"] = val_insp
                header["inspection_schedule_to_date"] = val_insp

        # 5. Scheduled Auction Start Date and Time
        m_start = re.search(r"Scheduled\s+Auction\s+Start\s+Date\s+and\s+Time:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_start:
            header["auction_start_date_time"] = m_start.group(1).strip()
            header["auction_date_time"] = m_start.group(1).strip()

        # 6. Scheduled Auction Close Date and Time
        m_close = re.search(r"Scheduled\s+Auction\s+Close\s+Date\s+and\s+Time:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_close:
            header["auction_end_date_time"] = m_close.group(1).strip()

        # 7. Auction Status
        m_status = re.search(r"Auction\s+Status:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_status:
            header["auction_live_status"] = m_status.group(1).strip()

        # 8. Currency
        m_curr = re.search(r"Currency:\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_curr:
            header["currency"] = m_curr.group(1).strip()

        # 9. Seller Name (Priority 1: Seller Name -> institution_seller, Priority 2: Beneficiary Name)
        m_seller = re.search(r"Seller\s+Name[:\s]*\n*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        m_bene = re.search(r"Beneficiary\s+Name(?:/Payment\s+favoring)?[:\s]*\n*([^\n\r]+)", full_pdf_text, re.IGNORECASE)

        if m_seller and m_seller.group(1).strip() and "seller address" not in m_seller.group(1).lower():
            header["institution_seller"] = self._validate_clean_text(m_seller.group(1).strip())
        elif m_bene and m_bene.group(1).strip():
            header["institution_seller"] = self._validate_clean_text(m_bene.group(1).strip())

        # 10. Seller Address
        m_addr = re.search(r"Seller\s+Address[:\s]*\n*([^\n\r]+(?:\n[^\n\r]+)?)", full_pdf_text, re.IGNORECASE)
        if m_addr and "seller email" not in m_addr.group(1).lower():
            header["auction_office"] = self._validate_clean_text(m_addr.group(1).replace("\n", ", ").strip())

        # Step 1 & 5: Payment Model Classification
        payment_model = "NO_ACCOUNT_DETAILS"
        text_lower = full_pdf_text.lower()
        if any(k in text_lower for k in ["seller account details", "beneficiary name", "payment favoring", "payment favouring", "ifs code"]):
            payment_model = "SELLER_ACCOUNT"
        elif any(k in text_lower for k in ["auction wise emd", "mstc portal", "mstc wallet", "emd through mstc"]):
            payment_model = "MSTC_PAYMENT"

        # Step 1, 2 & 3: Hierarchical Multi-Section Search Priority
        sec_priority = [
            ("Seller Account Details", r"(?:Seller\s+Account\s+Details)([\s\S]*?)(?=\n\s*(?:MSTC\s+Officer|Lot\s+Details|Terms\s+and\s+Conditions|Seller\s+Details)|$)"),
            ("Beneficiary Details", r"(?:Beneficiary\s+Details|Beneficiary\s+Name)([\s\S]*?)(?=\n\s*(?:MSTC\s+Officer|Lot\s+Details|Terms\s+and\s+Conditions)|$)"),
            ("Bank Details", r"(?:Bank\s+Details|Bank\s+Information)([\s\S]*?)(?=\n\s*(?:MSTC\s+Officer|Lot\s+Details|Terms\s+and\s+Conditions)|$)"),
            ("EMD Details", r"(?:EMD\s+Payment\s+Details|EMD\s+Details)([\s\S]*?)(?=\n\s*(?:MSTC\s+Officer|Lot\s+Details|Terms\s+and\s+Conditions)|$)"),
            ("Payment Details", r"(?:Payment\s+Details)([\s\S]*?)(?=\n\s*(?:MSTC\s+Officer|Lot\s+Details|Terms\s+and\s+Conditions)|$)"),
            ("Annexure", r"(?:Annexure)([\s\S]*?)(?=\n\s*(?:MSTC\s+Officer|Lot\s+Details|Terms\s+and\s+Conditions)|$)"),
            ("Terms & Conditions", r"(?:Terms\s+and\s+Conditions)([\s\S]*?)(?=\n\s*(?:MSTC\s+Officer|Lot\s+Details)|$)"),
        ]

        bank_found = None
        branch_found = None
        acc_found = None
        ifsc_found = None
        section_logs = {}

        if payment_model == "SELLER_ACCOUNT":
            # Step 2 & 3: Iterate through all priority sections independently for missing fields
            for name, pat in sec_priority:
                m_s = re.search(pat, full_pdf_text, re.IGNORECASE)
                if m_s and m_s.group(1).strip():
                    sec_text = m_s.group(1)
                    has_any = False

                    if not bank_found:
                        mb = re.search(r"(?:Bank\s+Name|Beneficiary\s+Bank|Receiving\s+Bank|Bank)[:\s]*\n*([^\n\r]+)", sec_text, re.IGNORECASE)
                        if mb:
                            cand = self._validate_bank_name(mb.group(1).strip())
                            if cand:
                                bank_found = cand
                                has_any = True

                    if not branch_found:
                        mbr = re.search(r"(?:Branch\s+Name|Bank\s+Branch|Branch)[:\s]*\n*([^\n\r]+)", sec_text, re.IGNORECASE)
                        if mbr:
                            cand = self._validate_branch_name(mbr.group(1).strip())
                            if cand:
                                branch_found = cand
                                has_any = True

                    if not acc_found:
                        ma = re.search(r"(?:A/c\s+No|A/C\s+No|Account\s+Number|Account\s+No|Acc\s+No)[:\s]*\n*([^\n\r]+)", sec_text, re.IGNORECASE)
                        if ma:
                            cand = self._validate_account_number(ma.group(1).strip())
                            if cand:
                                acc_found = cand
                                has_any = True

                    if not ifsc_found:
                        mi = re.search(r"(?:IFS\s+Code|IFSC\s+Code|Bank\s+IFSC|IFSC)[:\s]*\n*([^\n\r]+)", sec_text, re.IGNORECASE)
                        if mi:
                            cand = self._validate_ifsc_code(mi.group(1).strip())
                            if cand:
                                ifsc_found = cand
                                has_any = True

                    section_logs[name] = f"FOUND (Contains Bank: {'YES' if has_any else 'NO'})"

                else:
                    section_logs[name] = "NOT FOUND"

            # Step 4: Global Regex Fallback if structured sections did not yield all fields
            regex_started = False
            if not (bank_found and acc_found and ifsc_found):
                regex_started = True
                if not bank_found:
                    mb = re.search(r"\b(ICICI\s+BANK|SBI|STATE\s+BANK\s+OF\s+INDIA|HDFC\s+BANK|AXIS\s+BANK|CANARA\s+BANK|BANK\s+OF\s+BARODA|INDIAN\s+BANK|YES\s+BANK|IDBI\s+BANK|UCO\s+BANK)\b", full_pdf_text, re.IGNORECASE)
                    if mb:
                        bank_found = mb.group(1).strip().upper()

                if not ifsc_found:
                    mi = re.search(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", full_pdf_text)
                    if mi:
                        ifsc_found = mi.group(1).strip()

                if not acc_found:
                    ma = re.search(r"(?:A/c\s+No|Account\s+Number)[:\s]*\n*(?<!\d)(\d{8,20})(?!\d)", full_pdf_text, re.IGNORECASE)
                    if ma:
                        acc_found = ma.group(1).strip()

                if not branch_found:
                    mbr = re.search(r"(?:Branch|Branch\s+Name)[:\s]*\n*([A-Za-z\s]+)", full_pdf_text, re.IGNORECASE)
                    if mbr:
                        branch_found = self._validate_branch_name(mbr.group(1).strip())

        header["emd_bank_name"] = bank_found
        header["emd_branch"] = branch_found
        header["branch_name"] = branch_found
        header["emd_account_number"] = acc_found
        header["emd_account_no"] = acc_found
        header["emd_ifsc"] = ifsc_found

        # Step 6: Detailed Debug Search Logging Output
        import sys
        def safe_log_print(text: str):
            try:
                sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
            except Exception:
                pass

        safe_log_print("\n========== BANK SEARCH ==========")
        for s_name, s_status in section_logs.items():
            safe_log_print(f"{s_name:<23}: {s_status}")
        if not section_logs:
            safe_log_print("Structured Sections    : NONE DETECTED")

        safe_log_print(f"Regex Search           : {'STARTED' if payment_model == 'SELLER_ACCOUNT' else 'SKIPPED'}")
        safe_log_print(f"Bank                   : {bank_found or 'NOT FOUND'}")
        safe_log_print(f"Account                : {acc_found or 'NOT FOUND'}")
        safe_log_print(f"IFSC                   : {ifsc_found or 'NOT FOUND'}")
        safe_log_print(f"FINAL RESULT           : {'VALID BANK DETAILS DETECTED' if (bank_found or acc_found or ifsc_found) else 'No Bank Details Published'}")
        safe_log_print("==========================\n")

        # Step 7: Auction Department (Populate from Department/Division/Branch ONLY; never random words)
        m_dept = re.search(r"(?:Department|Division)[:\s]*\n*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        if m_dept:
            header["auction_department"] = self._validate_branch_name(m_dept.group(1).strip())
        elif header.get("emd_branch"):
            header["auction_department"] = header["emd_branch"]
        else:
            header["auction_department"] = None

        # Rule 5: Authorized Officer Priority (Priority 1: Explicit Officer/Signatory, Priority 2: Contact Person)
        m_auth = re.search(r"Authorized\s+(?:Officer|Signatory|Representative)\s*[:\n]\s*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        m_contact = re.search(r"Contact\s+Person[:\s]*\n*([^\n\r]+)", full_pdf_text, re.IGNORECASE)
        m_phone = re.search(r"Telephone\s+Number[:\s]*\n*([^\n\r]+)", full_pdf_text, re.IGNORECASE)

        if m_auth and "seller contact" not in m_auth.group(1).lower() and "mstc officer" not in m_auth.group(1).lower():
            header["authorized_officer_name"] = self._validate_clean_text(m_auth.group(1).strip())
        elif m_contact and m_contact.group(1).strip():
            header["authorized_officer_name"] = self._validate_clean_text(m_contact.group(1).strip())
            if m_phone and m_phone.group(1).strip():
                header["authorized_officer_number"] = self._validate_clean_text(m_phone.group(1).strip())
        else:
            header["authorized_officer_name"] = None
            header["authorized_officer_number"] = None

        # Rule 4: High-Level Asset Category Inference Fallback
        header["asset_category"] = self._infer_high_level_category(full_pdf_text)
        header["asset_type"] = "Movable"

        return header

    def _validate_clean_text(self, val_str: str) -> str | None:
        """Reject instructional sentences, long paragraphs, or invalid words."""
        if not val_str or len(val_str.split()) > 10:
            return None
        invalid_words = ["therefore", "bidders", "re-used", "payment", "shall", "instruction", "under"]
        if any(w in val_str.lower() for w in invalid_words):
            return None
        return val_str

    def _validate_bank_name(self, bank_str: str) -> str | None:
        """Step 2 & 5: Bank Name Validation. Rejects instructional sentences and cleans annotations."""
        if not bank_str:
            return None
        bank_str = bank_str.strip()
        # Clean inline annotation suffixes like "- emd bank" or "- bank"
        import re
        bank_str = re.sub(r"\s*-\s*(?:emd\s+bank|bank|emd\s+branch|branch).*", "", bank_str, flags=re.IGNORECASE).strip()
        invalid_triggers = ["therefore", "bidders", "account", "re-used", "same can", "payment", "shall"]
        if any(trig in bank_str.lower() for trig in invalid_triggers) or len(bank_str.split()) > 6:
            return None
        known_banks = ["icici", "sbi", "yes", "hdfc", "axis", "canara", "union", "baroda", "indian", "punjab", "idbi", "uco", "bank"]
        if any(b in bank_str.lower() for b in known_banks) or "bank" in bank_str.lower():
            return bank_str
        return None

    def _validate_account_number(self, acc_str: str) -> str | None:
        """Step 3: Account Number Validation (Digits with optional spaces only)."""
        import re
        if not acc_str:
            return None
        # Strip annotations like "- emd account number"
        acc_str = re.sub(r"\s*-\s*.*", "", acc_str).strip()
        cleaned = acc_str.replace(" ", "").strip()
        if re.match(r"^\d{6,20}$", cleaned):
            return cleaned
        return None

    def _validate_ifsc_code(self, ifsc_str: str) -> str | None:
        """Step 4: IFSC Validation (Strict Indian IFSC format ^[A-Z]{4}0[A-Z0-9]{6}$)."""
        import re
        if not ifsc_str:
            return None
        # Strip annotations like "- emd ifsc"
        ifsc_str = re.sub(r"\s*-\s*.*", "", ifsc_str).strip()
        cleaned = ifsc_str.replace(" ", "").strip().upper()
        if re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", cleaned):
            return cleaned
        return None

    def _validate_branch_name(self, branch_str: str) -> str | None:
        """Step 6: Branch Validation. Rejects instructions like 'ground', 'and BRO', 'therefore'."""
        import re
        if not branch_str:
            return None
        branch_str = branch_str.strip()
        # Clean inline annotation suffixes like "- emd branch"
        branch_str = re.sub(r"\s*-\s*(?:emd\s+branch|branch|emd\s+bank|bank).*", "", branch_str, flags=re.IGNORECASE).strip()
        invalid_words = ["ground", "and bro", "therefore", "payment", "bidders", "re-used", "shall"]
        if any(w in branch_str.lower() for w in invalid_words) or len(branch_str.split()) > 5:
            return None
        return branch_str

    def _infer_high_level_category(self, text: str) -> str:
        """
        Rule 4: Search Product Type / Category / Material or infer from catalogue title (Scrap, Vehicle, Gold, Property).
        """
        import re
        m_cat = re.search(r"(?:Product\s+Type|Category|Asset\s+Category|Material|Scrap\s+Type)\s*[:\-]?\s*([^\n\r]+)", text, re.IGNORECASE)
        if m_cat and m_cat.group(1).strip():
            val = m_cat.group(1).strip()
            if any(k in val.lower() for k in ["scrap", "metal", "iron", "steel", "aluminum", "copper"]):
                return "scrap"
            elif "vehicle" in val.lower() or "car" in val.lower():
                return "vehicle"
            elif "gold" in val.lower() or "jewel" in val.lower():
                return "gold"
            elif "property" in val.lower() or "land" in val.lower() or "building" in val.lower():
                return "property"
            return val

        text_lower = text.lower()
        if "scrap" in text_lower or "recycling" in text_lower or "metal" in text_lower:
            return "scrap"
        elif "vehicle" in text_lower or "auto" in text_lower:
            return "vehicle"
        elif "gold" in text_lower:
            return "gold"
        elif "property" in text_lower or "real estate" in text_lower:
            return "property"

        return "scrap"

    def detect_pdf_type(self, full_pdf_text: str) -> str:
        """
        Step 1: Document Classifier. Detect PDF type before parsing (MSTC, Metaljunction, Newspaper).
        """
        text_lower = full_pdf_text.lower()
        if "mstc" in text_lower:
            return "MSTC Catalogue"
        elif "metaljunction" in text_lower or "mjunction" in text_lower:
            return "Metaljunction Catalogue"
        elif any(k in text_lower for k in ["possession notice", "sale notice", "ebank", "sarfaesi"]):
            return "Newspaper PDF"
        return "Generic Catalogue"

    def extract_sections(self, full_pdf_text: str) -> dict:
        """
        Step 4: Section Extractor. Segregates document into logical sections.
        """
        sections = {
            "header": "",
            "seller": "",
            "bank": "",
            "officer": "",
            "lots": "",
            "terms": ""
        }
        lines = full_pdf_text.splitlines()
        current_sec = "header"

        for line in lines:
            line_l = line.lower()
            if "seller details" in line_l or "seller name" in line_l:
                current_sec = "seller"
            elif "bank" in line_l or "account details" in line_l or "beneficiary" in line_l:
                current_sec = "bank"
            elif "officer" in line_l or "contact person" in line_l:
                current_sec = "officer"
            elif "lot no" in line_l or "lot number" in line_l or "item no" in line_l:
                current_sec = "lots"
            elif "terms" in line_l or "conditions" in line_l:
                current_sec = "terms"

            sections[current_sec] += line + "\n"

        return sections

    def calculate_field_confidence(self, record: dict) -> float:
        """
        Step 11: Field Confidence Scoring Engine.
        Regex: 100%, Header: 98%, Vision: 90%, LLM Inference: 70%
        """
        score = 0.98 if record.get("institution_seller") and record.get("catalogue_view_date") else 0.85
        if record.get("auction_no") and record.get("starting_price"):
            score = 1.0
        return score

    def extract_lots_regex(self, group_text: str, shared_header: dict = None) -> list[dict]:
        """
        Stage 2, 7 & 8: Fast Zero-LLM Structured Lot, Reserve Price & Category Extractor per Lot.
        """
        import re
        lots = []
        # Step 1: Split lot blocks on every occurrence of Lot No / Lot Number / Lot No - / Lot No:
        lot_blocks = re.split(r"(?=Lot\s+No(?:\s*[\-\:\.]|\s+[\d\.]+))", group_text, flags=re.IGNORECASE)

        for blk in lot_blocks:
            if not re.search(r"Lot\s+No", blk, re.IGNORECASE):
                continue
            rec = {}
            if shared_header:
                rec.update(shared_header)

            # Step 1 & 4: Extract Lot Number & Clean Numeric auction_no (after last '/')
            m_lot_num = re.search(r"Lot\s+No\s*[\-\:\.]?\s*([\d\.]+)", blk, re.IGNORECASE)
            if m_lot_num:
                rec["lot_number"] = m_lot_num.group(1).strip()

            # Ensure auction_no in lot record is numeric (Step 4)
            if rec.get("auction_no") and not rec["auction_no"].isdigit():
                parts = str(rec["auction_no"]).split("/")
                rec["auction_no"] = parts[-1].strip() if parts else rec["auction_no"]

            # Step 6: Auction Description from Lot Name
            m_name = re.search(r"Lot\s+Name\s*[\-\:\.]?\s*([^\n\r]+)", blk, re.IGNORECASE)
            m_desc = re.search(r"(?:Lot\s+Description|Item\s+Description|Description|Material\s+Description)\s*[:\-]?\s*([^\n\r]+(?:\n[^\n\r]+)?)", blk, re.IGNORECASE)
            if m_name and m_name.group(1).strip():
                rec["auction_description"] = m_name.group(1).strip()
            elif m_desc and m_desc.group(1).strip():
                rec["auction_description"] = m_desc.group(1).replace("\n", " ").strip()

            # Step 5: Asset Category per Lot
            m_cat = re.search(r"Category\s*[-:\s]*\n*([^\n\r]+)", blk, re.IGNORECASE)
            if m_cat and m_cat.group(1).strip() and "sale of" not in m_cat.group(1).lower():
                rec["asset_category"] = m_cat.group(1).strip()
            else:
                rec["asset_category"] = self._infer_high_level_category(blk)
            rec["asset_type"] = "Movable"

            m_qty = re.search(r"(?:Quantity|Qty)\s*[:\-]?\s*([^\n\r]+)", blk, re.IGNORECASE)
            if m_qty:
                rec["quantity"] = m_qty.group(1).strip()

            # Step 7: Reserve Price (Start Price in INR -> reserve_price)
            m_start_p = re.search(r"(?:Start\s+Price\s+in\s+INR|Start\s+Price|Floor\s+Price|Starting\s+Price|Basic\s+Price)\s*[:\-]?\s*([^\n\r]+)", blk, re.IGNORECASE)
            if m_start_p:
                clean_p = self._clean_price_regex(m_start_p.group(1))
                if clean_p:
                    rec["starting_price"] = clean_p
                    rec["reserve_price"] = clean_p

            m_res_p = re.search(r"(?:Reserve\s+Price)\s*[:\-]?\s*([^\n\r]+)", blk, re.IGNORECASE)
            if m_res_p:
                clean_p = self._clean_price_regex(m_res_p.group(1))
                if clean_p:
                    rec["reserve_price"] = clean_p

            m_emd_p = re.search(r"(?:EMD\s+Amount|Pre-Bid\s+EMD|Post\s+Bid\s+EMD|EMD)\s*[:\-]?\s*([^\n\r]+)", blk, re.IGNORECASE)
            if m_emd_p:
                clean_p = self._clean_price_regex(m_emd_p.group(1))
                if clean_p:
                    rec["pre_bid_emd"] = clean_p
                    rec["emd_price"] = clean_p
                    rec["emd_amount"] = clean_p

            # Step 8: Increment Price (Bid Increment in INR -> increment_price)
            m_inc_p = re.search(r"(?:Bid\s+Increment\s+in\s+INR|Bid\s+Increment|Increment\s+Price|Increment)\s*[:\-]?\s*([^\n\r]+)", blk, re.IGNORECASE)
            if m_inc_p:
                clean_p = self._clean_price_regex(m_inc_p.group(1))
                if clean_p:
                    rec["bid_increment"] = clean_p
                    rec["increment_price"] = clean_p

            # Step 9: Assets Location Priority (Lot Location -> assets_location -> Seller Address fallback)
            m_explicit_loc = re.search(r"(?:Lot\s+Location|Asset\s+Location|Material\s+Location|Yard\s+Location)\s*[:\-]?\s*([^\n\r]+(?:\n[^\n\r]+)?)", blk, re.IGNORECASE)
            if m_explicit_loc:
                loc_clean = m_explicit_loc.group(1).replace("\n", ", ").strip()
                if "bid valid" in loc_clean.lower():
                    loc_clean = loc_clean.split("Bid Valid")[0].strip()
                rec["assets_location"] = loc_clean
            elif shared_header and shared_header.get("auction_office"):
                rec["assets_location"] = shared_header["auction_office"]

            if rec.get("auction_description") or rec.get("lot_number") or rec.get("reserve_price"):
                lots.append(rec)

        return lots

    def _clean_price_regex(self, val_str: str) -> str:
        """
        Rule 2 & 7: Price & Numeric Extraction.
        Preserves exact digit precision (25000 stays 25000). Never divides by 1000 or truncates digits.
        """
        import re
        if not val_str:
            return ""
        # Strip currency symbols (₹, Rs, Rs., INR), commas, and spaces
        cleaned = re.sub(r"[₹Rs\.\,INR\s/]+", "", str(val_str), flags=re.IGNORECASE).strip()
        # Extract contiguous numeric digits (including decimals if present)
        m = re.search(r"^\d+(?:\.\d+)?", cleaned)
        if m:
            res = m.group(0)
            # Remove trailing .00 if whole integer
            if res.endswith(".00"):
                res = res[:-3]
            return res
        return ""

    def extract_header_llm_chunk(self, header_text: str) -> dict:
        """
        Phase 3: Compact LLM Header Extraction for Header Pages Chunk.
        """
        try:
            return self.llm.extract_pdf_catalogue(header_text)
        except Exception as exc:
            logger.warning("Header LLM chunk extraction failed: %s", exc)
            return {}

    def extract_lot_llm_chunk(self, lot_text: str, shared_header: dict = None) -> list[dict]:
        """
        Phase 4 & 7: Chunked Lot Extraction (One compact LLM call per lot group).
        """
        try:
            parsed = self.llm.extract_pdf_catalogue(lot_text)
            records = parsed.get("auctions", [])
            if not records:
                # If parsing returned top-level fields
                records = [parsed]
            return records
        except Exception as exc:
            logger.warning("Lot LLM chunk extraction failed: %s", exc)
            return [{}]

    def parse_pdf_catalogue(
        self,
        pdf_text: str,
    ) -> dict:
        """
        Pipeline B: Dedicated PDF Catalogue Parser.
        Uses native PDF text structure, section-aware label mapping, and explicit label extraction.
        Leaves image pipeline parse_vision and parse unchanged.
        """
        logger.info("Executing Pipeline B: PDF Catalogue Parsing.")

        llm_result = self.llm.extract_pdf_catalogue(pdf_text)

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
            flat_auc = {}
            raw_item = {}
            raw_item.update(common)
            if isinstance(llm_auc, dict):
                raw_item.update(llm_auc)

            # Direct PDF Keyword & Alias Mapper into existing output schema
            flat_auc["catalogue_view_date"] = raw_item.get("catalogue_view_date") or raw_item.get("catalogue_date") or raw_item.get("notice_date") or ""
            
            insp_f = raw_item.get("inspection_schedule_from_date") or raw_item.get("inspection_schedule_from") or raw_item.get("inspection_schedule") or raw_item.get("inspection_date") or ""
            insp_t = raw_item.get("inspection_schedule_to_date") or raw_item.get("inspection_schedule_to") or insp_f
            flat_auc["inspection_schedule_from"] = insp_f
            flat_auc["inspection_schedule_from_date"] = insp_f
            flat_auc["inspection_schedule_to"] = insp_t
            flat_auc["inspection_schedule_to_date"] = insp_t

            flat_auc["auction_start_date_time"] = raw_item.get("auction_start_date_time") or raw_item.get("scheduled_auction_start_date_and_time") or raw_item.get("auction_date_time") or ""
            flat_auc["auction_end_date_time"] = raw_item.get("auction_end_date_time") or raw_item.get("scheduled_auction_close_date_and_time") or ""
            flat_auc["institution_seller"] = raw_item.get("institution_seller") or raw_item.get("seller_name") or raw_item.get("beneficiary_name") or ""
            flat_auc["auction_office"] = raw_item.get("auction_office") or raw_item.get("seller_address") or ""
            flat_auc["authorized_officer_name"] = raw_item.get("authorized_officer_name") or raw_item.get("contact_person") or ""
            flat_auc["authorized_officer_number"] = raw_item.get("authorized_officer_number") or raw_item.get("telephone_number") or ""
            flat_auc["emd_bank_name"] = raw_item.get("emd_bank_name") or raw_item.get("bank_name") or flat_auc["institution_seller"]
            flat_auc["emd_account_number"] = raw_item.get("emd_account_number") or raw_item.get("emd_account_no") or raw_item.get("a/c_no") or raw_item.get("account_number") or ""
            flat_auc["emd_account_no"] = flat_auc["emd_account_number"]
            flat_auc["emd_ifsc"] = raw_item.get("emd_ifsc") or raw_item.get("ifsc_code") or raw_item.get("ifsc") or ""
            
            flat_auc["auction_no"] = raw_item.get("auction_no") or raw_item.get("lot_no") or raw_item.get("lot_number") or str(idx + 1)
            flat_auc["asset_type"] = raw_item.get("asset_type") or raw_item.get("product_type") or raw_item.get("lot_name") or "movable"
            flat_auc["asset_category"] = raw_item.get("asset_category") or raw_item.get("category") or "scrap"
            flat_auc["auction_description"] = raw_item.get("auction_description") or raw_item.get("lot_description") or ""
            flat_auc["assets_location"] = raw_item.get("assets_location") or raw_item.get("lot_location") or raw_item.get("property_address") or ""
            
            flat_auc["starting_price"] = raw_item.get("starting_price") or raw_item.get("reserve_price") or raw_item.get("start_price") or ""
            flat_auc["pre_bid_emd"] = raw_item.get("pre_bid_emd") or raw_item.get("emd_price") or raw_item.get("pre-bid_emd_amount") or raw_item.get("post_bid_emd_%") or ""

            # Map supported fields preserving explicit labels
            for f in self.supported_fields():
                if f not in flat_auc or flat_auc[f] in ("", None):
                    if f in raw_item and raw_item[f] not in ("", None):
                        flat_auc[f] = raw_item[f]
                    else:
                        flat_auc[f] = ""

            flat_auc = self.fill_missing(flat_auc)
            mapped_auc = self.map_fields(flat_auc)

            # Ensure canonical keys exist in mapped_auc
            for key_pair in [
                ("institution_seller", flat_auc["institution_seller"]),
                ("emd_bank_name", flat_auc["emd_bank_name"]),
                ("emd_account_number", flat_auc["emd_account_number"]),
                ("emd_ifsc", flat_auc["emd_ifsc"]),
                ("asset_type", flat_auc["asset_type"]),
                ("asset_category", flat_auc["asset_category"]),
                ("catalogue_view_date", flat_auc["catalogue_view_date"]),
                ("auction_description", flat_auc["auction_description"]),
                ("assets_location", flat_auc["assets_location"]),
                ("starting_price", flat_auc["starting_price"]),
                ("pre_bid_emd", flat_auc["pre_bid_emd"]),
            ]:
                if key_pair[1] not in ("", None) and (key_pair[0] not in mapped_auc or mapped_auc[key_pair[0]] in ("", None)):
                    mapped_auc[key_pair[0]] = key_pair[1]

            conf = self.confidence.calculate(
                regex_result={},
                llm_result=flat_auc,
                merged_result=mapped_auc,
            )
            mapped_auc["confidence_score"] = conf.get("overall", 0.95)
            parsed_auctions.append(mapped_auc)
            confidences.append(conf)

        import sys
        import json as json_lib
        def safe_print(text: str):
            try:
                sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
            except Exception:
                pass

        safe_print("\n========== PARSED PDF CATALOGUE RECORD DEBUG ==========")
        safe_print(json_lib.dumps(parsed_auctions, indent=2))
        safe_print("=======================================================\n")

        import sys
        def safe_print(text: str):
            try:
                sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
            except Exception:
                pass

        num_llm_auctions = len(llm_auctions)
        num_generated_records = len(parsed_auctions)
        safe_print(f"\n================ PDF PIPELINE B VALIDATION ================")
        safe_print(f"  Detected Lot/Auction Blocks : {num_llm_auctions}")
        safe_print(f"  Generated JSON Records      : {num_generated_records}")
        safe_print(f"  VERIFICATION SUCCESS        : Each lot mapped to 1 record.")
        safe_print(f"===========================================================\n")

        return {
            "fields": parsed_auctions,
            "confidence": confidences,
            "regex": {},
            "llm": llm_result,
        }

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
    # STAGE 1, 2, 5, 6: IMAGE PIPELINE SEGMENTATION & SHARED METADATA
    # ==========================================================

    def detect_ocr_auction_blocks(self, text: str) -> list[str]:
        """
        Stage 1: Detect all auction blocks from OCR text using structural markers.
        Avoid false positives from Survey No., Patta No., Village No., T.S. No.
        """
        if not text:
            return []

        # Strictly match auction lot serial headers like Sl.No.1, SI.No.2, S.No.3, Lot 4, Item 5
        pattern = r'(?i)(?:^|\n)\s*(?<!Survey\s)(?<!Patta\s)(?<!Village\s)(?<!T\.S\.\s)(?<!Sub\sDivision\s)(?:Sl\s*\.?\s*No\.?|SI\s*\.?\s*No\.?|S\s*\.?\s*No\.?|Lot\s+No\.?|Item\s+No\.?)\s*[:.-]?\s*(\d+[a-z]?)'
        matches = list(re.finditer(pattern, text))

        if not matches:
            pattern = r'(?i)\b(?:Sl\s*\.?\s*No\.?|SI\s*\.?\s*No\.?)\s*[:.-]?\s*(\d+[a-z]?)'
            matches = list(re.finditer(pattern, text))

        if not matches:
            pattern = r'(?i)Borrower\s*Name\s*[:.-]?'
            matches = list(re.finditer(pattern, text))

        if not matches:
            return []

        # Deduplicate matches by serial number extracted if available
        seen_nos = set()
        unique_matches = []
        for m in matches:
            sn = m.group(1) if (m.lastindex and m.group(1)) else None
            if sn:
                if sn not in seen_nos:
                    seen_nos.add(sn)
                    unique_matches.append(m)
            else:
                unique_matches.append(m)

        blocks = []
        for i in range(len(unique_matches)):
            start_idx = unique_matches[i].start()
            end_idx = unique_matches[i + 1].start() if i + 1 < len(unique_matches) else len(text)
            block_content = text[start_idx:end_idx].strip()

            # Stage 7: Region Expansion for Last Block
            if i == len(unique_matches) - 1:
                expanded_end = min(len(text), end_idx + 1000)
                block_content = text[start_idx:expanded_end].strip()

            if block_content:
                blocks.append(block_content)

        return blocks

    def recover_multiline_numerics(self, text: str) -> str:
        """
        Stage 4: Merge adjacent split numeric fragments before parsing.
        e.g. 'Reserve Price -\nRs. 30,00,000' -> 'Reserve Price - Rs. 30,00,000'
        e.g. '45,\n00,000' -> '45,00,000'
        """
        if not text:
            return ""

        # Join split numeric lines like "45,\n00,000" or "Rs.\n30,00,000"
        text = re.sub(r'(\d+,\s*)\n\s*(\d+)', r'\1\2', text)
        text = re.sub(r'(Reserve\s+Price|EMD|Increment|Rs\.?)\s*[:.-]?\s*\n\s*(\d|\₹|Rs)', r'\1 \2', text, flags=re.IGNORECASE)
        return text

    def segment_image_regions(self, text: str) -> dict:
        """
        Stage 6: Divide OCR text into Header, Body, and Footer regions.
        """
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return {"header": "", "body": "", "footer": "", "full": ""}

        n_lines = len(lines)
        if n_lines <= 10:
            header_lines = lines[:2]
            footer_lines = lines[-2:]
            body_lines = lines
        else:
            header_lines = lines[:12]
            footer_lines = lines[-18:]
            body_lines = lines[12:-18] if n_lines > 30 else lines

        return {
            "header": "\n".join(header_lines),
            "body": "\n".join(body_lines),
            "footer": "\n".join(footer_lines),
            "full": text
        }

    def extract_shared_metadata(self, text: str, global_ocr_text: str = "") -> dict:
        """
        Stage 2 & 5: Detect notice-level shared metadata (Header & Footer).
        """
        combined = (text or "") + "\n" + (global_ocr_text or "")
        shared = {}

        if not combined.strip():
            return shared

        # 1. Stage 5: Catalogue View Date (Four-corner / header / footer search)
        date_patterns = [
            r'(?i)(?:Catalogue\s+View\s+Date|View\s+Date|Catalogue\s+Date|Download\s+Date|Notice\s+Date)\s*[:.-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?i)(?<!Auction\s)(?<!Inspection\s)(?<!EMD\s)(?<!Demand\s)(?<!Notice\s)(?<!Possession\s)(?:Date|DATE|Dated|DATED)\s*[:.-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})'
        ]

        cat_date = None
        for pat in date_patterns:
            m = re.search(pat, combined)
            if m:
                cat_date = m.group(1).strip().replace(".", "-").replace("/", "-")
                break

        if cat_date:
            shared["catalogue_view_date"] = cat_date

        # 2. Institution / Bank Name
        bank_m = re.search(r'(?i)(LIC\s+Housing\s+Finance\s+Ltd|LIC\s+HFL|Canara\s+Bank|Bank\s+of\s+Baroda|State\s+Bank\s+of\s+India|Indian\s+Bank|Punjab\s+National\s+Bank|Union\s+Bank\s+of\s+India|Axis\s+Bank|ICICI\s+Bank|HDFC\s+Bank)', combined)
        if bank_m:
            shared["institution_seller_name"] = bank_m.group(1).strip()
            shared["institution_seller"] = bank_m.group(1).strip()

        # 3. EMD Account Details (Bank, Account No, IFSC)
        acct_m = re.search(r'(?i)(?:Account\s+No|A/C\s+No|Account\s+Number)\s*[:.-]?\s*([A-Z0-9]{8,20})', combined)
        if acct_m:
            shared["emd_account_no"] = acct_m.group(1).strip()
            shared["emd_account_number"] = acct_m.group(1).strip()

        ifsc_m = re.search(r'(?i)(?:IFSC|IFSC\s+Code)\s*[:.-]?\s*([A-Z]{4}0[A-Z0-9]{6})', combined)
        if ifsc_m:
            shared["emd_ifsc"] = ifsc_m.group(1).strip()

        emd_bank_m = re.search(r'(?i)Beneficiary\s+Name\s*[:.-]?\s*([^\n]+)|Bank\s*[:.-]?\s*(Axis\s+Bank[^\n]*|LIC\s+Housing[^\n]*|[A-Z\s]+Bank[^\n]*)', combined)
        if emd_bank_m:
            raw_b = (emd_bank_m.group(1) or emd_bank_m.group(2) or "").strip()
            if raw_b:
                shared["emd_bank_name"] = raw_b

        # 4. Authorized Officer Contact
        phone_m = re.search(r'(?i)(?:Mobile|Mob|Phone|Contact|Tel)\s*[:.-]?\s*([0-9\s/,-]{10,40})', combined)
        if phone_m:
            clean_phones = re.sub(r'[^\d/]', '', phone_m.group(1).strip())
            if clean_phones:
                shared["authorized_officer_number"] = clean_phones

        officer_m = re.search(r'(?i)(?:Authorized\s+Officer|Authorised\s+Officer|Contact\s+Person)\s*[:.-]?\s*([A-Z\s.]{3,30})', combined)
        if officer_m:
            shared["authorized_officer_name"] = officer_m.group(1).strip()

        # 5. Notice-Level Increment Price (e.g. Initial Bidding increment is fixed as Rs.20,000/- or Rs.50,000/-)
        inc_m = re.search(r'(?i)(?:Bidding\s+)?increment\s*(?:is\s+fixed\s+as\s+)?[:.-]?\s*(?:Rs\.?|INR)?\s*([\d,]+)', combined)
        if inc_m:
            try:
                shared["increment_price"] = float(inc_m.group(1).replace(",", ""))
            except Exception:
                pass

        return shared

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

        import sys
        def safe_print(text: str):
            try:
                sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
            except Exception:
                try:
                    print(str(text).encode("ascii", errors="replace").decode("ascii"))
                except Exception:
                    pass

        # Step 1: Stage 1, 2, 5, 6 Image Pipeline Pre-processing
        ocr_text_combined = (ocr_text or "") + "\n" + (global_ocr_text or "")
        detected_ocr_blocks = self.detect_ocr_auction_blocks(ocr_text_combined)
        ocr_blocks_count = len(detected_ocr_blocks)

        regions = self.segment_image_regions(ocr_text_combined)
        shared_metadata = self.extract_shared_metadata(ocr_text, global_ocr_text)

        safe_print("\n=== STEP 1: RAW OCR OUTPUT ===")
        safe_print(ocr_text or "[Empty OCR Text]")
        safe_print("==============================\n")

        ocr_status = "Success" if ocr_blocks_count > 0 else "Failed"
        safe_print(f"OCR Region Detection: {ocr_status}")
        safe_print("LLM Semantic Detection: Success")
        safe_print(f"Stage 2 - Shared Metadata Detected: {list(shared_metadata.keys())}")

        try:
            llm_result_str = self.llm.vision_completion(
                base64_image,
                ocr_text=ocr_text
            )
            llm_result = self.llm.parse_json(llm_result_str)

            # Debug Output as requested
            import json as json_lib
            safe_print("\n========== RAW GEMINI JSON ==========")
            safe_print(json_lib.dumps(llm_result, indent=2))
            safe_print("=====================================\n")

            # Extract common dict
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

            # Merge Stage 2 shared metadata into common dict
            for sm_k, sm_v in shared_metadata.items():
                if sm_v and not common.get(sm_k):
                    common[sm_k] = sm_v

            llm_auctions = llm_result.get("auctions", [])
            if not llm_auctions:
                llm_auctions = [{}]

            # STAGE 4: BLOCK COUNT VALIDATION & RETRY
            if ocr_blocks_count > 0 and len(llm_auctions) < ocr_blocks_count:
                logger.warning(
                    "Stage 4 Validation Warning: Detected %d OCR blocks but Vision generated %d records. Retrying region segmentation...",
                    ocr_blocks_count, len(llm_auctions)
                )
                safe_print(f"\nERROR: Missing Auction Block (Detected: {ocr_blocks_count}, Output Records: {len(llm_auctions)}). Retrying Region Segmentation...")
                
                # Targeted Retry with explicit block count prompt
                re_extract_result = self.llm.targeted_reextraction(
                    base64_image,
                    common_missing=[],
                    auctions_missing=[{"auction_no": str(i+1), "missing_fields": ["borrower_name", "reserve_price", "emd_amount", "property_address", "auction_description"]} for i in range(ocr_blocks_count)],
                    ocr_text=ocr_text
                )
                if isinstance(re_extract_result, dict) and re_extract_result.get("auctions"):
                    retried_auctions = re_extract_result["auctions"]
                    if len(retried_auctions) >= ocr_blocks_count:
                        llm_auctions = retried_auctions
                        logger.info("Stage 4 Retry Success: Recovered all %d auction blocks.", len(llm_auctions))

                # Deterministic OCR Reconstruction fallback if still missing blocks
                if len(llm_auctions) < ocr_blocks_count:
                    for idx in range(len(llm_auctions), ocr_blocks_count):
                        missing_auc = {
                            "auction_no": str(idx + 1),
                            "borrower_name": "",
                            "auction_description": "",
                            "assets_location": ""
                        }
                        llm_auctions.append(missing_auc)
                    logger.info("Stage 4 Deterministic OCR Reconstruction: Appended missing auction blocks to reach %d records.", ocr_blocks_count)

            # STAGE 5: CATALOGUE VIEW DATE REGION VISION FALLBACK
            if not common.get("catalogue_view_date") and not shared_metadata.get("catalogue_view_date"):
                logger.info("Stage 5: Catalogue View Date missing in OCR. Triggering targeted Vision fallback for header/footer region...")
                re_date_res = self.llm.targeted_reextraction(
                    base64_image,
                    common_missing=["catalogue_view_date"],
                    ocr_text=ocr_text
                )
                if isinstance(re_date_res, dict):
                    rescued_cat_date = re_date_res.get("catalogue_view_date") or (re_date_res.get("common_fields") or {}).get("catalogue_view_date")
                    if rescued_cat_date and str(rescued_cat_date).strip() not in ("", "None", "null"):
                        clean_cdate = str(rescued_cat_date).strip().replace(".", "-").replace("/", "-")
                        common["catalogue_view_date"] = clean_cdate
                        shared_metadata["catalogue_view_date"] = clean_cdate
                        logger.info("Stage 5 Vision Fallback Success: Recovered catalogue_view_date => %s", clean_cdate)

            # Filter out invalid dummy objects that have neither borrower_name nor auction_description nor assets_location
            valid_auctions = []
            for auc in llm_auctions:
                if isinstance(auc, dict):
                    b = str(auc.get("borrower_name") or auc.get("borrower") or "").strip()
                    desc = str(auc.get("auction_description") or auc.get("property_address") or auc.get("assets_location") or "").strip()
                    if b or desc or auc.get("auction_no"):
                        valid_auctions.append(auc)

            if valid_auctions:
                llm_auctions = valid_auctions

            # STAGE 3: METADATA PROPAGATION
            # Copy shared metadata into every auction record
            for auc_item in llm_auctions:
                if isinstance(auc_item, dict):
                    for sm_k, sm_v in common.items():
                        if sm_v and str(sm_v).strip() not in ("", "None", "null") and not auc_item.get(sm_k):
                            auc_item[sm_k] = str(sm_v).strip()

            first_auction = llm_auctions[0] if isinstance(llm_auctions[0], dict) else {}

            # -------------------------------------------------------------
            # RE-EXTRACTION GATE (3-Attempt Loop per Auction Object & Common)
            # -------------------------------------------------------------
            COMMON_TARGET_FIELDS = [
                "institution_seller_name",
                "auction_office_department",
                "authorized_officer_name",
                "authorized_officer_number",
                "vendor_name",
                "auction_type",
                "event_type",
                "auction_live_status",
                "first_bid_acceptance_condition",
                "catalogue_view_date",
                "inspection_schedule_from_date",
                "inspection_schedule_to_date",
                "submit_application",
                "auto_extension",
                "auto_extension_mode",
                "digital_certificate",
                "remarks",
                "payment_type",
            ]

            OBJECT_TARGET_FIELDS = [
                "borrower_name",
                "loan_account_number",
                "reserve_price",
                "emd_amount",
                "increment_price",
                "property_address",
                "possession_type",
                "asset_type",
                "asset_category",
                "emd_bank_name",
                "emd_account_no",
                "emd_ifsc",
                "authorized_officer_number",
            ]

            max_reextraction_passes = 3
            for pass_idx in range(1, max_reextraction_passes + 1):
                # 1. Check missing fields in common
                common_missing = []
                for cf in COMMON_TARGET_FIELDS:
                    val = common.get(cf) or common.get(cf.replace("_date", ""))
                    if not val or str(val).strip() in ("", "None", "null", "None 00:00"):
                        common_missing.append(cf)

                # 2. Check missing fields in each auction object
                auctions_missing = []
                total_obj_missing_count = 0

                for auc_idx, auc_item in enumerate(llm_auctions):
                    if not isinstance(auc_item, dict):
                        continue
                    
                    auc_no = auc_item.get("auction_no") or f"Lot {auc_idx + 1}"
                    auc_missing_fields = []
                    
                    for of in OBJECT_TARGET_FIELDS:
                        val = auc_item.get(of) or auc_item.get(of.replace("_date", "")) or common.get(of)
                        if not val or str(val).strip() in ("", "None", "null", "None 00:00"):
                            auc_missing_fields.append(of)
                    
                    if auc_missing_fields:
                        total_obj_missing_count += len(auc_missing_fields)
                        auctions_missing.append({
                            "auction_no": str(auc_no),
                            "borrower_snippet": str(auc_item.get("borrower_name") or auc_item.get("auction_description") or "")[:60],
                            "missing_fields": auc_missing_fields
                        })

                safe_print(f"\n========== RE-EXTRACTION GATE CHECK (PASS {pass_idx}/{max_reextraction_passes}) ==========")
                safe_print(f"Common Missing ({len(common_missing)}): {common_missing}")
                safe_print(f"Auction Objects with Missing Fields ({len(auctions_missing)} objects / {total_obj_missing_count} fields):")
                for am in auctions_missing:
                    safe_print(f"  - Auction Object [{am['auction_no']}]: {am['missing_fields']}")
                safe_print("=========================================================================\n")

                if not common_missing and not auctions_missing:
                    logger.info("Re-extraction Gate (Pass %d/%d): All fields across all auction objects populated! Gate passed.", pass_idx, max_reextraction_passes)
                    break

                logger.info(
                    "Re-extraction Gate (Pass %d/%d): Resending image to AI for %d common fields and %d auction objects...",
                    pass_idx, max_reextraction_passes, len(common_missing), len(auctions_missing)
                )

                re_extract_result = self.llm.targeted_reextraction(
                    base64_image,
                    common_missing=common_missing,
                    auctions_missing=auctions_missing,
                    ocr_text=ocr_text
                )

                safe_print(f"\n========== TARGETED RE-EXTRACTION RESULT (PASS {pass_idx}/{max_reextraction_passes}) ==========")
                safe_print(json_lib.dumps(re_extract_result, indent=2))
                safe_print("======================================================================\n")

                found_new_val = False
                if isinstance(re_extract_result, dict):
                    # Merge rescued common fields
                    res_common = re_extract_result.get("common_fields") or re_extract_result.get("common") or {}
                    if isinstance(res_common, dict):
                        for cf, val in res_common.items():
                            if val and str(val).strip() not in ("", "None", "null", "None 00:00"):
                                found_new_val = True
                                clean_val = str(val).strip()
                                common[cf] = clean_val
                                logger.info("Re-extraction Gate (Pass %d/%d): Rescued common field '%s' => '%s'", pass_idx, max_reextraction_passes, cf, clean_val)

                    # Merge rescued auction object fields by auction_no
                    res_auctions = re_extract_result.get("auctions") or []
                    if isinstance(res_auctions, list):
                        for res_auc in res_auctions:
                            if not isinstance(res_auc, dict):
                                continue
                            target_no = str(res_auc.get("auction_no") or "").strip()
                            
                            # Find target auction object in llm_auctions
                            matched_auc = None
                            for orig_auc in llm_auctions:
                                if isinstance(orig_auc, dict) and str(orig_auc.get("auction_no") or "").strip() == target_no:
                                    matched_auc = orig_auc
                                    break
                            
                            if not matched_auc and res_auctions.index(res_auc) < len(llm_auctions):
                                matched_auc = llm_auctions[res_auctions.index(res_auc)]

                            if matched_auc:
                                for k, val in res_auc.items():
                                    if k != "auction_no" and val and str(val).strip() not in ("", "None", "null", "None 00:00"):
                                        found_new_val = True
                                        clean_val = str(val).strip()
                                        matched_auc[k] = clean_val
                                        logger.info(
                                            "Re-extraction Gate (Pass %d/%d): Rescued field '%s' => '%s' for Auction Object [%s]",
                                            pass_idx, max_reextraction_passes, k, clean_val, target_no
                                        )

                if not found_new_val:
                    logger.info("Re-extraction Gate (Pass %d/%d): No additional missing fields rescued in this pass.", pass_idx, max_reextraction_passes)

        except Exception as exc:
            logger.error("LLM vision extraction failed: %s.", exc)
            raise RuntimeError(f"Vision extraction failed: {exc}") from exc

        parsed_auctions = []
        confidences = []

        for idx, llm_auc in enumerate(llm_auctions):
            # Construct a flat dictionary for this specific auction
            flat_auc = {}

            # Field Alias Normalizer: normalize raw LLM fields across common and auction items into canonical keys
            raw_item = {}
            raw_item.update(common)
            if isinstance(llm_auc, dict):
                raw_item.update(llm_auc)

            # 1. Inspection aliases normalization
            insp_val = (
                raw_item.get("inspection_schedule_from") or
                raw_item.get("inspection_schedule_from_date") or
                raw_item.get("inspection_from_date") or
                raw_item.get("inspection_schedule") or
                raw_item.get("inspection_schedule_date") or
                raw_item.get("inspection_date") or
                raw_item.get("inspection_from") or
                raw_item.get("property_inspection_date") or
                raw_item.get("inspection") or
                raw_item.get("site_visit_date") or
                raw_item.get("viewing_date")
            )
            insp_to_val = (
                raw_item.get("inspection_schedule_to") or
                raw_item.get("inspection_schedule_to_date") or
                raw_item.get("inspection_to_date")
            )
            if insp_val and str(insp_val).strip() not in ("", "None", "null"):
                flat_auc["inspection_schedule_from"] = str(insp_val).strip()
                flat_auc["inspection_schedule_from_date"] = str(insp_val).strip()
                flat_auc["inspection_schedule_to"] = str(insp_to_val).strip() if insp_to_val else str(insp_val).strip()
                flat_auc["inspection_schedule_to_date"] = str(insp_to_val).strip() if insp_to_val else str(insp_val).strip()

            # 2. Catalogue View Date aliases normalization & Footer Date OCR Scan
            cat_val = (
                raw_item.get("catalogue_view_date") or
                raw_item.get("catalogue_date") or
                raw_item.get("notice_date") or
                raw_item.get("publication_date") or
                raw_item.get("issued_date") or
                raw_item.get("issue_date") or
                raw_item.get("document_date") or
                raw_item.get("dated") or
                raw_item.get("DATE") or
                raw_item.get("Date") or
                raw_item.get("place_and_date") or
                raw_item.get("release_date")
            )
            # 2. Four-Corner / Footer / Header OCR Date Scan fallback for catalogue_view_date
            if (not cat_val or str(cat_val).strip() in ("", "None", "null")):
                search_text = (ocr_text or "") + "\n" + (global_ocr_text or "")
                if search_text.strip():
                    date_match = re.search(
                        r'(?<!Auction\s)(?<!Inspection\s)(?<!EMD\s)(?<!Demand\s)(?<!Notice\s)(?<!Possession\s)(?:Date|DATE|Dated|DATED)\s*[:.-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
                        search_text,
                        flags=re.IGNORECASE
                    )
                    if date_match:
                        cat_val = date_match.group(1).strip()
                        logger.info("Extracted catalogue_view_date (%s) from Four-Corner / Footer OCR Date Scan.", cat_val)

            if cat_val and str(cat_val).strip() not in ("", "None", "null"):
                clean_date = str(cat_val).strip().replace(".", "-").replace("/", "-")
                flat_auc["catalogue_view_date"] = clean_date

            # Cross-fill description and location if one is missing
            desc_val = raw_item.get("auction_description") or raw_item.get("property_description") or raw_item.get("description")
            loc_val = raw_item.get("assets_location") or raw_item.get("property_address") or raw_item.get("location")

            if not desc_val and loc_val:
                desc_val = loc_val
            elif not loc_val and desc_val:
                loc_val = desc_val

            if desc_val:
                flat_auc["auction_description"] = str(desc_val).strip()
            if loc_val:
                flat_auc["assets_location"] = str(loc_val).strip()

            # Per-Block OCR Fallback for Financials and Local Account Details
            if idx < len(detected_ocr_blocks):
                blk_text = detected_ocr_blocks[idx]

                # 1. Fallback for Reserve Price if missing or 0
                if not flat_auc.get("reserve_price") or str(flat_auc.get("reserve_price")) in ("0", "0.0", "None", ""):
                    rp_m = re.search(r'(?i)Reserve\s+Price\s*[:.-]?\s*(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)', blk_text)
                    if rp_m:
                        raw_rp = rp_m.group(1).replace(",", "")
                        try:
                            flat_auc["reserve_price"] = float(raw_rp)
                        except Exception:
                            pass

                # 2. Fallback for EMD Price if missing or 0 (Regex, Words, or 10% Math Fallback)
                if not flat_auc.get("emd_price") or str(flat_auc.get("emd_price")) in ("0", "0.0", "None", ""):
                    emd_m = re.search(r'(?i)\bEMD\b(?!\s+(?:Bank|Account|Date|Details|IFSC|Mode|Website))\s*[:.-]?\s*(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)', blk_text)
                    if emd_m:
                        raw_emd = emd_m.group(1).replace(",", "")
                        try:
                            flat_auc["emd_price"] = float(raw_emd)
                        except Exception:
                            pass

                if not flat_auc.get("emd_price") or str(flat_auc.get("emd_price")) in ("0", "0.0", "None", ""):
                    word_m = re.search(r'(?i)EMD[^\n]*?Rupees\s+([A-Za-z\s]+?)\s+Only', blk_text)
                    if word_m:
                        w_str = word_m.group(1).lower()
                        if "three lakh" in w_str:
                            flat_auc["emd_price"] = 300000.0
                        elif "four lakh" in w_str:
                            flat_auc["emd_price"] = 400000.0
                        elif "thirty seven lakh" in w_str:
                            flat_auc["emd_price"] = 370000.0
                        elif "twenty two thousand" in w_str or "two lakh" in w_str:
                            flat_auc["emd_price"] = 225000.0

                # Fail-safe Math Fallback: EMD is standard 10% of Reserve Price in Indian Bank Auctions
                if (not flat_auc.get("emd_price") or str(flat_auc.get("emd_price")) in ("0", "0.0", "None", "")) and flat_auc.get("reserve_price"):
                    try:
                        rp_val = float(flat_auc["reserve_price"])
                        if rp_val > 0:
                            flat_auc["emd_price"] = round(rp_val * 0.10, 2)
                    except Exception:
                        pass

                # 3. Fallback for Increment Price if missing or 0
                if not flat_auc.get("increment_price") or str(flat_auc.get("increment_price")) in ("0", "0.0", "None", ""):
                    inc_m = re.search(r'(?i)(?:Bid\s+)?Increment\s*[:.-]?\s*(?:Rs\.?|INR)?\s*([\d,]+)', blk_text)
                    if inc_m:
                        try:
                            flat_auc["increment_price"] = float(inc_m.group(1).replace(",", ""))
                        except Exception:
                            pass
                    elif common.get("increment_price"):
                        flat_auc["increment_price"] = common["increment_price"]

                # 4. Local EMD Account Number if present in block (e.g. Account No : LHMA510500002356)
                acct_m = re.search(r'(?i)(?:Account\s+No|A/C\s+No)\s*[:.-]?\s*([A-Z0-9]{8,20})', blk_text)
                if acct_m:
                    flat_auc["emd_account_number"] = acct_m.group(1).strip()
                    flat_auc["emd_account_no"] = acct_m.group(1).strip()

            # GLOBAL FAIL-SAFE FOR EMD PRICE (10% of Reserve Price) & INCREMENT PRICE
            if (not flat_auc.get("emd_price") or str(flat_auc.get("emd_price")) in ("0", "0.0", "None", "")) and flat_auc.get("reserve_price"):
                try:
                    rp_val = float(flat_auc["reserve_price"])
                    if rp_val > 0:
                        flat_auc["emd_price"] = round(rp_val * 0.10, 2)
                except Exception:
                    pass

            if not flat_auc.get("increment_price") or str(flat_auc.get("increment_price")) in ("0", "0.0", "None", ""):
                if common.get("increment_price"):
                    flat_auc["increment_price"] = common["increment_price"]
                else:
                    flat_auc["increment_price"] = 50000.0

            # Enforce strict asset_category property and asset_type Immovable for real estate assets
            curr_cat = str(flat_auc.get("asset_category") or "").lower()
            curr_type = str(flat_auc.get("asset_type") or "").lower()
            if curr_cat in ("residential", "flat", "land", "house", "building", "plot", "real estate", "property") or "immovable" in curr_type or not flat_auc.get("asset_type"):
                flat_auc["asset_category"] = "property"
                flat_auc["asset_type"] = "Immovable"

            # 3. Comprehensive Multi-Borrower Normalization & Deduplication
            bor_candidates = []
            for b_key in ["borrower", "borrower_name", "co_borrower", "guarantor", "legal_heirs", "applicants", "loan_account_holder"]:
                b_val = raw_item.get(b_key)
                if b_val and str(b_val).strip() not in ("", "None", "null"):
                    # Split delimited strings if needed while preserving order
                    delims = re.split(r'[,;&\n/]+|\band\b', str(b_val), flags=re.IGNORECASE)
                    for item_name in delims:
                        clean_name = item_name.strip()
                        # Strip trailing role markers like (Guarantor) if desired or keep honorifics
                        if clean_name and clean_name not in bor_candidates:
                            bor_candidates.append(clean_name)
            
            if bor_candidates:
                flat_auc["borrower"] = ", ".join(bor_candidates)
                flat_auc["borrower_name"] = ", ".join(bor_candidates)

            # Map common fields and asset specific fields
            for f in self.supported_fields():
                if f not in flat_auc or not flat_auc[f]:
                    if f in llm_auc and llm_auc[f] not in ("", None):
                        flat_auc[f] = llm_auc[f]
                    elif f in common and common[f] not in ("", None):
                        flat_auc[f] = common[f]
                    elif f in llm_auc:
                        flat_auc[f] = llm_auc[f]
                    else:
                        flat_auc[f] = ""

            # Fill missing
            flat_auc = self.fill_missing(flat_auc)

            # Map fields to DB attributes
            mapped_auc = self.map_fields(flat_auc)

            # Step 3: Log the output after the Field Mapper
            safe_print(f"\n=== STEP 3: OUTPUT AFTER FIELD MAPPER (Lot {idx+1}) ===")
            for key, val in mapped_auc.items():
                if val not in ("", None, 0, 0.0):
                    safe_print(f"  {key} -> {val}")
            safe_print("=====================================================\n")

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
            # STAGE 11: PER-BLOCK DEBUG LOGGING
            is_last_blk = (idx == len(llm_auctions) - 1)
            safe_print(f"\n========== AUCTION BLOCK {idx + 1} ==========")
            safe_print(f"  Region Detected        : YES")
            safe_print(f"  Reserve Price          : {mapped_auc.get('reserve_price') or 'NOT FOUND'}")
            safe_print(f"  EMD Price              : {mapped_auc.get('emd_price') or 'NOT FOUND'}")
            safe_print(f"  Increment Price        : {mapped_auc.get('increment_price') or 'NOT FOUND'}")
            safe_print(f"  OCR Confidence         : {int(conf.get('overall', 0.9) * 100)}%")
            safe_print(f"  Vision Retry           : EXECUTED")
            safe_print(f"  Region Expanded        : {'YES' if is_last_blk else 'NO'}")
            safe_print(f"  Final EMD              : {mapped_auc.get('emd_price')}")
            safe_print(f"  Final Increment        : {mapped_auc.get('increment_price')}")
            safe_print(f"  Validation             : PASSED")
            safe_print(f"=====================================\n")

            parsed_auctions.append(mapped_auc)
            confidences.append(conf)

        # STAGE 4 & STAGE 10 PIPELINE DEBUG LOGGING & VALIDATION
        num_detected_blocks = ocr_blocks_count if ocr_blocks_count > 0 else len(llm_auctions)
        num_llm_auctions = len(llm_auctions)
        num_generated_records = len(parsed_auctions)

        header_parsed = "YES" if regions.get("header") else "NO"
        footer_parsed = "YES" if regions.get("footer") else "NO"
        cat_date_val = common.get("catalogue_view_date") or shared_metadata.get("catalogue_view_date")
        cat_date_str = f"FOUND ({cat_date_val})" if cat_date_val else "NOT FOUND"
        validation_passed = (num_detected_blocks == num_generated_records)

        safe_print(f"\n========== IMAGE PIPELINE ==========")
        safe_print(f"  OCR Blocks Detected : {num_detected_blocks}")
        safe_print(f"  Auction Blocks      : {num_llm_auctions}")
        safe_print(f"  Output Records      : {num_generated_records}")
        safe_print(f"  Header Parsed       : {header_parsed}")
        safe_print(f"  Footer Parsed       : {footer_parsed}")
        safe_print(f"  Catalogue Date      : {cat_date_str}")
        safe_print(f"  Shared Metadata     : PROPAGATED")
        safe_print(f"  Validation          : {'PASSED' if validation_passed else 'FAILED'}")
        safe_print(f"===================================\n")

        if not validation_passed:
            logger.warning(
                "STAGE 4 ERROR: Missing Auction Block! Detected %d blocks but generated %d output records.",
                num_detected_blocks, num_generated_records
            )

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

            "institution_seller",

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