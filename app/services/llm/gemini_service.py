"""
Gemini LLM Service.

Uses Google Gemini LLM to extract structured
auction information directly from images.
"""

from __future__ import annotations

import json
import logging
import os
import requests

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class GeminiService:
    """
    Gemini LLM wrapper.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Initializing Gemini Service."
        )

        self.api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = settings.gemini_model or "gemini-1.5-flash"
        self.temperature = 0.0
        self.max_tokens = 4096

    # ==========================================================
    # Ready Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Check Gemini client settings.
        """
        return bool(self.api_key)

    # ==========================================================
    # Model Information
    # ==========================================================

    def model_info(
        self,
    ) -> dict:
        """
        Return current model details.
        """
        return {
            "provider": "Gemini",
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    # ==========================================================
    # Supported Fields
    # ==========================================================

    def supported_fields(
        self,
    ) -> list[str]:
        """
        Fields expected from LLM.
        """
        return [
            # Event and Institution details
            "institution_seller_name",
            "auction_office_department",
            "vendor_name",
            "authorized_officer_name",
            "authorized_officer_number",
            "email",
            # New fields
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
            "pre_bid_emd",
            "starting_price",
            "emd_price",
            
            # Auction Mechanics and Dates
            "auction_type",
            "event_type",
            "auction_live_status",
            "first_bid_acceptance_condition",
            "currency",
            "auction_start_date_time",
            "auction_end_date_time",
            "submit_application",
            "inspection_schedule_from",
            "inspection_schedule_to",
            "auto_extension",
            "auto_extension_mode",
            "auction_extend_time_mins",

            # EMD and Payment Details
            "emd_bank_name",
            "emd_account_no",
            "emd_ifsc",
            "payment_type",

            # Portal Specific Fields
            "remarks",

            # Auction specific fields
            "auction_no",
            "asset_id",
            "auction_id",
            "borrower_name",
            "co_borrower",
            "guarantor",
            "loan_account_number",
            "asset_category",
            "asset_type",
            "auction_description",
            "property_type",
            "possession_type",
            "property_area",
            "reserve_price",
            "emd_amount",
            "increment_price",

            "property_address",
            "district",
            "state",
            "pin_code",
        ]

    # ==========================================================
    # Empty Record
    # ==========================================================

    def empty_record(
        self,
    ) -> dict:
        """
        Empty extraction result matching the new comprehensive schema.
        """
        return {
            "event_and_institution_details": {
                "institution_seller_name": "",
                "auction_office_department": "",
                "vendor_name": "",
                "authorized_officer_name": "",
                "authorized_officer_number": "",
                "email": "",

                "institution_seller": "",
                "auction_office": "",
                "auction_department": ""
            },
            "auction_mechanics_and_dates": {
                "auction_type": "",
                "event_type": "",
                "auction_live_status": "",
                "first_bid_acceptance_condition": "",
                "currency": "INR",
                "catalogue_view_date": "",
                "auction_start_date_time": "",
                "auction_end_date_time": "",
                "submit_application": "",
                "inspection_schedule_from": "",
                "inspection_schedule_to": "",
                "auto_extension": "",
                "auto_extension_mode": "",
                "auction_extend_time_mins": ""
            },
            "emd_and_payment_details": {
                "payment_type": ""
            },
            "portal_specific_fields": {
                "digital_certificate": "",

                "remarks": ""
            },
            "auctions": [
                {
                    "auction_no": "",
                    "asset_id": "",
                    "auction_id": "",
                    "borrower_name": "",
                    "co_borrower": "",
                    "guarantor": "",
                    "loan_account_number": "",
                    "asset_category": "",
                    "asset_type": "",
                    "auction_description": "",
                    "property_type": "",
                    "possession_type": "",
                    "property_area": "",
                    "reserve_price": "",
                    "emd_amount": "",
                    "increment_price": "",

                    "property_address": "",
                    "district": "",
                    "state": "",
                    "pin_code": "",
                    "emd_bank_name": "",
                    "emd_account_no": "",
                    "emd_ifsc": "",
                    "authorized_officer_name": "",
                    "authorized_officer_number": "",
                    
                    # Category-specific fields inside individual auction items
                    "asset_subcategory": "",
                    "full_payment_balance": "",
                    "delivery_of_material_taken": "",
                    "quantity": "",
                    "units": "",
                    "start_floor_price": "",
                    "vendor_name": "",
                    "sum_of_carat_18": "",
                    "sum_of_carat_19": "",
                    "sum_of_carat_20": "",
                    "sum_of_carat_21": "",
                    "sum_of_carat_22": "",
                    "sum_of_carat_23": "",
                    "sum_of_carat_24": "",
                    "sum_of_net_weight_total": "",
                    "sum_of_gross_weight_total": "",
                    "year": "",
                    "reg_no": "",
                    "repo_date": "",
                    "km_driven": "",
                    "rc": "",
                    "chassis_number": "",
                    "yard_rent_percent": "",
                    
                    # Aliases for parser matching
                    "starting_price": "",
                    "pre_bid_emd": "",
                    "emd_price": ""
                }
            ]
        }

    def schema_text(
        self,
    ) -> str:
        """
        JSON schema as formatted text.
        """
        return json.dumps(
            self.empty_record(),
            indent=4,
        )

    # ==========================================================
    # Vision Completion (Direct Scrape)
    # ==========================================================

    def vision_completion(
        self,
        base64_image: str,
        ocr_text: str = "",
    ) -> str:
        """
        Send base64 image directly to Gemini API and return structured JSON.
        """
        logger.info(
            "Calling Gemini API directly for direct visual scraping."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        system_instruction = (
            "You are a highly defensive, zero-tolerance data-extraction vision pipeline specialized in structural document intelligence. You process highly diverse Indian bank auction notices, asset disposal catalogues, regulatory public announcements, and internal digital admin forms. Your primary directive is 100% data fidelity. You must never invent, assume, approximate, or hallucinate any data point.\n\n"
            "### CRITICAL ADAPTABILITY & STRUCTURAL PARSING RULES:\n"
            "1. UNIVERSAL LAYOUT AGNOSTICISM: Treat every input as structurally unique. Inputs range from messy, unstructured newspaper columns and multi-page PDF tables to highly structured web portal forms with dropdowns and text boxes. Parse the text dynamically based on spatial proximity, field labels, and visual alignment.\n"
            "2. RIGOROUS DECOMPOSITION: When data entities (such as multi-party names or combined address blocks) are densely packed, map out the semantic transitions perfectly. Dissect these strings cleanly into their unique JSON fields.\n"
            "3. MULTI-ENTITY ARRAY SEQUENCING (CRITICAL): Do NOT map table rows 1-to-1 to JSON objects. If multiple items listed under a single table row or block are collectively auctioned (such as a plant & machinery list of 12 items collectively auctioned as a single lot), extract them as a single auction object using the combined total reserve price (e.g. 39177800) and combined total EMD (e.g. 3917780). Otherwise, if a single table row or section lists multiple separate properties with their own individual reserve prices (e.g. 'Property No. 1' and 'Property No. 2' having separate prices), you MUST generate a SEPARATE object in the 'auctions' list/array for each property/asset. Label their auction_no fields with suffixes (e.g., '2a' and '2b' or '2.1' and '2.2'). For example, you must generate one object for Property No. 1 (with reserve_price 30504500 and emd_amount 3050450, labeled auction_no '2a') and a second object for Property No. 2 (with reserve_price 42469000 and emd_amount 4246900, labeled auction_no '2b'). Never group multiple separate reserve prices or combine separate properties into a single object. Each property/asset must have its own unique auction object in the list.\n"
            "4. TABULAR HORIZONTAL ALIGNMENT: When notices are printed in table format, strictly align fields horizontally. Do not mix property addresses, EMD amounts, or reserve prices across different rows. Ensure a cell's extracted data corresponds exactly to the row's identifier/borrower.\n"
            "5. MULTI-COLUMN NOTICE PAGES (CRITICAL): Some notice pages are printed in a multi-column format (e.g. left column and right column side-by-side). You MUST read both columns from top to bottom. Visually identify every single serial number block (which may have OCR spelling variations like 'Sl.No.', 'SI.No.', 'S1.No.', 'S.No.') in both columns, and generate a SEPARATE object in the 'auctions' array for each serial number (e.g., Sl.No.1, SI.No.2, SI.No.3, SI.No.4, SI.No.5, SI.No.6). Never omit any columns or skip sections on the right/left side of the page.\n\n"
            "### MANDATORY ZERO-HALLUCINATION & NORMALIZATION CONTROLS:\n"
            "1. STRICT FILTERS FOR ABSENT DATA (CRITICAL): If a specific column, dropdown, or field defined in the JSON schema is missing, blank, not visible, or omitted from the source document, you MUST return an empty string \"\" for that field. You are strictly forbidden from providing mock data, placeholder variables, filler values, or template content.\n"
            "2. ENFORCED MATHEMATICAL SCALE MULTIPLIERS: Inspect all structural layout sections, column headers, footnotes, and margins for scale context keys (e.g., \"Amount in Lakhs\", \"(Rs. in Crore)\"). When a multiplier context key is verified, you must mathematically compute and expand the field value into a fully detailed, literal whole integer string (e.g., \"11.16\" Crores -> \"111600000\").\n"
            "3. FINANCIAL TEXT CHARACTER STRIPPING: Strip all financial string extractions (Reserve Price, EMD, Increment) of character noise, including commas, spaces, currency indicators (₹, Rs, Rs., INR), or trailing expressions (/-). Return exclusively pure numeric digit strings (e.g., \"₹ 92,77,200/-\" must be returned exactly as \"9277200\").\n"
            "4. COMPLETE LITERAL GEOGRAPHIC PARSING (CRITICAL): Capture the COMPLETE, exact, full multi-line location/address text inside \"assets_location\" (and \"property_address\"). Include all village, tehsil, road, landmark, city, district, pin code, and additional borrower/mortgagor/guarantor address details listed for the asset in the notice. Do NOT truncate, shorten, summarize, or split the location across OCR line breaks.\n\n"
            "### STRICT STANDARDIZATION & VALUE CONSTRAINTS:\n"
            "1. asset_type: Must be strictly one of: \"movable\" or \"immovable\". Do not use any other words.\n"
            "2. asset_category: Must be strictly one of: \"scrap\", \"gold\", \"vehicle\", \"pearl\", or \"property\".\n"
            "   - If asset_type is \"movable\", asset_category must be one of \"scrap\", \"gold\", \"vehicle\", or \"pearl\".\n"
            "   - If asset_type is \"immovable\", asset_category must be \"property\".\n"
            "3. AUCTION TYPE: Must be strictly \"Forward\", \"Reverse\", or \"Tender\". If not found, return \"\".\n"
            "4. AUTO EXTENSION: Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "5. AUTO EXTENSION MODE: Must be strictly \"Infinite\" or \"Custom\". If not mentioned, default to \"\".\n"
            "6. AUCTION LIVE STATUS: Must be strictly \"Live\", \"Reschedule\", \"Not Active\", or \"Cancel\". If not mentioned, default to \"\".\n"
            "7. FIRST BID ACCEPTANCE CONDITION: Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "8. PAYMENT TYPE: Extract the raw payment mode/type printed in the notice (e.g. \"RTGS/ NEFT\", \"DD\", \"Cheque\", \"Amount\", \"Transaction Value\"). For Property, choose strictly from \"Amount\" or \"Transaction Value\".\n"
            "9. ARE YOU INTERESTED?: Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "10. DATES & TIMES FORMATTING: Format all date and time fields (including \"auction_start_date_time\", \"auction_end_date_time\", \"submit_application\", \"inspection_schedule_from\", \"inspection_schedule_to\", \"repo_date\", \"catalogue_view_date\") strictly in standard format \"DD-MM-YYYY HH:MM\" or \"DD-MM-YYYY\" if no time is available.\n"
            "11. PER-AUCTION ACCOUNT DETAILS: Notice images typically list separate \"ACCOUNT DETAILS\" (Bank Name, Account No, IFSC Code) for EMD deposit. Extract EMD Bank Name independently from the Bank Name listed in the account details section (e.g. \"Canara Bank\"). Do NOT derive or leave EMD Bank Name empty; extract it independently from the notice under \"emd_bank_name\". Extract account number under \"emd_account_no\" and IFSC under \"emd_ifsc\".\n"
            "12. SEMANTIC DATE CLASSIFICATION (CRITICAL - NO HARDCODING):\n"
            "    - Every date in the document must be classified based strictly on surrounding labels, headings, and semantic meaning rather than page order or fixed document layout:\n"
            "    - Inspection Schedule (\"inspection_schedule_from\", \"inspection_schedule_to\"): Populate ONLY if the document explicitly describes an inspection schedule associated with semantic context like 'Inspection', 'Inspection Schedule', 'Property Inspection', 'Inspection Date', 'Inspection From/To', 'Asset Inspection', 'Site Visit', or 'Material Inspection'. If no explicit inspection details are present, you MUST return empty string \"\". NEVER infer or copy inspection dates from Notice Date, Publication Date, Advertisement Date, Signing Date, or Auction/EMD dates.\n"
            "    - Catalogue View Date (\"catalogue_view_date\"): Classify dates associated with document publication, notice date, advertisement date, document issue, signing date, or 'Place & Date' near the Authorized Officer signature block as \"catalogue_view_date\". Format as \"DD-MM-YYYY\". Do NOT reuse this date for inspection fields.\n"
            "    - Auction Start & End Dates (\"auction_start_date_time\", \"auction_end_date_time\"): Map dates explicitly labeled as auction date, e-auction schedule, or auction start/end time.\n"
            "    - Submit Application / EMD Deadline (\"submit_application\"): Map dates explicitly labeled as EMD submission deadline, last date of receipt of EMD, or application submission deadline.\n"
            "    - ZERO-DUPLICATION & DISAMBIGUATION: Assign each extracted date to only ONE business category field based on its highest semantic confidence. Never duplicate one extracted date across unrelated fields."
            "13. QUANTITY AND UNITS EXTRACTION (CRITICAL):\n"
            "    - When a notice specifies quantity (e.g. 'Qty - 01 Set', 'Qty - 01 Lot'), extract numeric quantity (e.g. \"1\") into \"quantity\" and unit string (e.g. \"Set\" or \"Lot\") into \"units\". If representing the entire lot, extract \"quantity\": \"1\", \"units\": \"Set\" (or \"Lot\").\n"
            "14. EXACT MATCHING FOR CATEGORY METADATA FIELDS:\n"
            "    - \"institution_seller\": Notice-wide institution or seller bank name (replaces notice-wide bank name).\n"
            "    - \"auction_office\": Notice-wide branch or auction office name.\n"
            "    - \"auction_department\": Notice-wide department or branch dept name.\n"
            "    - \"digital_certificate\": Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "    - \"catalogue_view_date\": Store the notice publication date/release date printed lower down/at the bottom of the page. Do NOT confuse it with the auction date. Format as \"DD-MM-YYYY\".\n"
            "    - \"vendor_name\": Choose strictly from: \"ABI\", \"AS\", \"TESTEMP\", \"BINUKUMAR\", \"FSTEMP\", \"TEST EMPS\", \"TEST EMP\".\n"
            "    - \"asset_subcategory\": Choose strictly from: \"Compressors\", \"E-Waste\", \"Used and Unused Machineries\", \"Wood Scrap\", \"Car\", \"LKI\" (for scrap), or \"Car\" (for vehicle).\n"
            "    - \"sum_of_carat_18\" to \"sum_of_carat_24\": Extract the exact carat weight value or flag (e.g. \"Y\" or \"-\") for gold.\n"
            "    - \"sum_of_net_weight_total\", \"sum_of_gross_weight_total\": Extract total gold weight details.\n"
            "    - \"year\", \"reg_no\", \"repo_date\", \"km_driven\", \"rc\", \"chassis_number\", \"yard_rent_percent\": Extract for vehicles.\n"
            "    - \"event_type\": Choose strictly from: \"Insurance Salvage\", \"REPO\", \"Sarfaesi\", \"DRT\", \"NCLT\", \"Consumer/Seller\", \"SARFAESI ACT\", \"kjno\", \"binnukutty\", \"qwerty\", \"bbbb\"."
        )

        prompt = (
            "Execute a pixel-perfect, deterministic scan of the provided asset auction document or web form. Analyze the spatial text structures dynamically and translate all verified document data points exactly into the provided comprehensive JSON schema structure.\n\n"
            "Apply strict character normalization to financial strings, compute explicit header-level scale multipliers (Crores/Lakhs) into absolute integers, and generate separate array objects for multi-line tabular entries.\n\n"
            "If ANY target schema field is not present, blank, or unreadable in the document, assign it a strict default empty value of \"\". Do not append any filler content or mock markers. Output only the clean, raw JSON payload.\n\n"
        )
        if ocr_text:
            prompt += f"To assist your visual scanning and prevent digit confusion, here is the raw OCR text extracted from the document:\n<ocr_text>\n{ocr_text}\n</ocr_text>\n\n"
            
        prompt += f"{self.schema_text()}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_instruction}\n\n{prompt}"
                        },
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
                "maxOutputTokens": 32768
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                # Check for rate limit / quota exhaustion (429) or temporary server unavailability (503)
                if response.status_code in (429, 503):
                    if attempt < max_retries:
                        retry_seconds = 10.0 if response.status_code == 503 else 35.0
                        try:
                            error_data = response.json()
                            err_msg = error_data.get("error", {}).get("message", "").lower()
                            if "quota" in err_msg or "limit" in err_msg or "exceeded" in err_msg:
                                logger.warning("Gemini API key is quota exhausted / rate limited: %s. Aborting retries.", err_msg)
                                raise RuntimeError(f"Gemini API quota exceeded: {error_data.get('error', {}).get('message')}")
                            details = error_data.get("error", {}).get("details", [])
                            for detail in details:
                                if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                                    delay_str = detail.get("retryDelay", "35s")
                                    if delay_str.endswith("s"):
                                        retry_seconds = float(delay_str[:-1]) + 2.0
                                    break
                        except RuntimeError:
                            raise
                        except Exception:
                            logger.warning("Failed to parse retry delay from Gemini response. Using default fallback.")
                        
                        logger.warning(
                            "Gemini API returned %d (Attempt %d/%d). Retrying in %.2f seconds...",
                            response.status_code, attempt + 1, max_retries + 1, retry_seconds
                        )
                        import time
                        time.sleep(retry_seconds)
                        continue
                    else:
                        logger.error("Exceeded maximum retries (Rate Limit / Unavailable).")
                        raise RuntimeError(f"Gemini API error: {response.text}")

                if response.status_code != 200:
                    logger.error("Gemini API request failed with status: %d - %s", response.status_code, response.text)
                    raise RuntimeError(f"Gemini API returned error status {response.status_code}: {response.text}")
                
                # If we get here, it's a 200 OK
                break
            except requests.exceptions.RequestException as exc:
                exc_str = str(exc).lower()
                if any(x in exc_str for x in ["getaddrinfo", "name resolution", "connection refused", "failed to resolve", "ssl", "eof", "timeout"]):
                    logger.error("Critical network/SSL connection failure: %s. Aborting retries.", exc)
                    raise exc
                if attempt < max_retries:
                    logger.warning("Network request failed: %s. Retrying in 5 seconds...", exc)
                    import time
                    time.sleep(5)
                    continue
                else:
                    raise exc

        try:
            res_data = response.json()
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned in Gemini response.")

            logger.info("Candidate metadata: %s", {k: v for k, v in candidates[0].items() if k != 'content'})
            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts:
                raise ValueError("No content parts returned in Gemini response candidate.")

            content = content_parts[0].get("text", "")
            logger.info("Gemini response received.")
            return content

        except Exception as exc:
            logger.exception("Gemini API response parsing failed.")
            raise RuntimeError(f"Gemini Error : {exc}") from exc

    # ==========================================================
    # Text-Based Extraction
    # ==========================================================

    def extract(
        self,
        text: str,
    ) -> dict:
        """
        Extract structured data from text using Gemini LLM.
        """
        logger.info("Calling Gemini API for text-based extraction.")

        system_instruction = (
            "You are a highly defensive, zero-tolerance data-extraction text pipeline specialized in structural document intelligence. You process Indian bank auction notices. Your primary directive is 100% data fidelity. You must never invent, assume, approximate, or hallucinate any data point.\n\n"
            "### STRICT STANDARDIZATION & VALUE CONSTRAINTS:\n"
            "1. asset_type: Must be strictly one of: \"movable\" or \"immovable\". Do not use any other words.\n"
            "2. asset_category: Must be strictly one of: \"scrap\", \"gold\", \"vehicle\", \"pearl\", or \"property\".\n"
            "   - If asset_type is \"movable\", asset_category must be one of \"scrap\", \"gold\", \"vehicle\", or \"pearl\".\n"
            "   - If asset_type is \"immovable\", asset_category must be \"property\".\n"
            "3. AUCTION TYPE: Must be strictly \"Forward\", \"Reverse\", or \"Tender\". If not found, return \"\".\n"
            "4. AUTO EXTENSION: Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "5. AUTO EXTENSION MODE: Must be strictly \"Infinite\" or \"Custom\". If not mentioned, default to \"\".\n"
            "6. AUCTION LIVE STATUS: Must be strictly \"Live\", \"Reschedule\", \"Not Active\", or \"Cancel\". If not mentioned, default to \"\".\n"
            "7. FIRST BID ACCEPTANCE CONDITION: Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "8. PAYMENT TYPE: Extract the raw payment mode/type printed in the notice (e.g. \"RTGS/ NEFT\", \"DD\", \"Cheque\", \"Amount\", \"Transaction Value\"). For Property, choose strictly from \"Amount\" or \"Transaction Value\".\n"
            "9. ARE YOU INTERESTED?: Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "10. DATES & TIMES FORMATTING: Format all date and time fields (including \"auction_start_date_time\", \"auction_end_date_time\", \"submit_application\", \"inspection_schedule_from\", \"inspection_schedule_to\", \"repo_date\", \"catalogue_view_date\") strictly in standard format \"DD-MM-YYYY HH:MM\" or \"DD-MM-YYYY\" if no time is available.\n"
            "11. EXACT MATCHING FOR CATEGORY METADATA FIELDS:\n"
            "    - \"institution_seller\": Notice-wide institution or seller bank name (replaces notice-wide bank name).\n"
            "    - \"auction_office\": Notice-wide branch or auction office name.\n"
            "    - \"auction_department\": Notice-wide department or branch dept name.\n"
            "    - \"digital_certificate\": Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "    - \"catalogue_view_date\": Store the notice publication date/release date printed lower down/at the bottom of the page. Do NOT confuse it with the auction date. Format as \"DD-MM-YYYY\".\n"
            "    - \"vendor_name\": Choose strictly from: \"ABI\", \"AS\", \"TESTEMP\", \"BINUKUMAR\", \"FSTEMP\", \"TEST EMPS\", \"TEST EMP\".\n"
            "    - \"asset_subcategory\": Choose strictly from: \"Compressors\", \"E-Waste\", \"Used and Unused Machineries\", \"Wood Scrap\", \"Car\", \"LKI\" (for scrap), or \"Car\" (for vehicle).\n"
            "    - \"sum_of_carat_18\" to \"sum_of_carat_24\": Extract the exact carat weight value or flag (e.g. \"Y\" or \"-\") for gold.\n"
            "    - \"sum_of_net_weight_total\", \"sum_of_gross_weight_total\": Extract total gold weight details.\n"
            "    - \"year\", \"reg_no\", \"repo_date\", \"km_driven\", \"rc\", \"chassis_number\", \"yard_rent_percent\": Extract for vehicles.\n"
            "    - \"event_type\": Choose strictly from: \"Insurance Salvage\", \"REPO\", \"Sarfaesi\", \"DRT\", \"NCLT\", \"Consumer/Seller\", \"SARFAESI ACT\", \"kjno\", \"binnukutty\", \"qwerty\", \"bbbb\".\n\n"
            "Output exclusively RAW, VALID JSON text matching the schema format below.\n"
            "DO NOT wrap the output payload inside markdown fences or code blocks. The output stream must start exactly with '{' and end with '}'."
        )

        prompt = (
            f"Extract all verified document data points exactly into the provided comprehensive JSON schema structure from the text below.\n\n"
            f"<text>\n{text}\n</text>\n\n"
            f"{self.schema_text()}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_instruction}\n\n{prompt}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
                "maxOutputTokens": 4096
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)

                # Check for rate limit / quota exhaustion (429) or temporary server unavailability (503)
                if response.status_code in (429, 503):
                    if attempt < max_retries:
                        retry_seconds = 10.0 if response.status_code == 503 else 35.0
                        try:
                            error_data = response.json()
                            err_msg = error_data.get("error", {}).get("message", "").lower()
                            if "quota" in err_msg or "limit" in err_msg or "exceeded" in err_msg:
                                logger.warning("Gemini API key is quota exhausted / rate limited: %s. Aborting retries.", err_msg)
                                raise RuntimeError(f"Gemini API quota exceeded: {error_data.get('error', {}).get('message')}")
                            details = error_data.get("error", {}).get("details", [])
                            for detail in details:
                                if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                                    delay_str = detail.get("retryDelay", "35s")
                                    if delay_str.endswith("s"):
                                        retry_seconds = float(delay_str[:-1]) + 2.0
                                    break
                        except RuntimeError:
                            raise
                        except Exception:
                            logger.warning("Failed to parse retry delay from Gemini response. Using default fallback.")

                        logger.warning(
                            "Gemini API returned %d (Attempt %d/%d). Retrying in %.2f seconds...",
                            response.status_code, attempt + 1, max_retries + 1, retry_seconds
                        )
                        import time
                        time.sleep(retry_seconds)
                        continue
                    else:
                        logger.error("Exceeded maximum retries (Rate Limit / Unavailable).")
                        raise RuntimeError(f"Gemini API error: {response.text}")

                if response.status_code != 200:
                    logger.error("Gemini API request failed with status: %d - %s", response.status_code, response.text)
                    raise RuntimeError(f"Gemini API returned error status {response.status_code}: {response.text}")

                break
            except requests.exceptions.RequestException as exc:
                exc_str = str(exc).lower()
                if any(x in exc_str for x in ["getaddrinfo", "name resolution", "connection refused", "failed to resolve", "ssl", "eof", "timeout"]):
                    logger.error("Critical network/SSL connection failure: %s. Aborting retries.", exc)
                    raise exc
                if attempt < max_retries:
                    logger.warning("Network request failed: %s. Retrying in 5 seconds...", exc)
                    import time
                    time.sleep(5)
                    continue
                else:
                    raise exc

        try:
            res_data = response.json()
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned in Gemini response.")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts:
                raise ValueError("No content parts returned in Gemini response candidate.")

            content = content_parts[0].get("text", "")
            return self.parse_json(content)

        except Exception as exc:
            logger.exception("Gemini API response parsing failed.")
            raise RuntimeError(f"Gemini Error : {exc}") from exc

    # ==========================================================
    # Parse JSON
    # ==========================================================

    def parse_json(
        self,
        response: str,
    ) -> dict:
        """
        Convert JSON string into dictionary.
        """
        if not response:
            return self.empty_record()

        import json_repair
        clean_res = response.strip()

        # Remove markdown code block wraps if present
        if clean_res.startswith("```"):
            lines = clean_res.split("\n")
            if lines[0].strip().startswith("```json") or lines[0].strip().startswith("```"):
                lines = lines[1:-1]
            clean_res = "\n".join(lines).strip()

        # Try standard json loads first
        try:
            return json.loads(clean_res)
        except Exception:
            # Fall back to robust json_repair
            try:
                repaired = json_repair.repair_json(clean_res, return_objects=True)
                if isinstance(repaired, dict):
                    return repaired
            except Exception as exc:
                logger.error("Failed to repair malformed JSON. Raw response: %s", clean_res)
                logger.exception("JSON repair failure.")
        
        return self.empty_record()

    def close(
        self,
    ) -> None:
        pass
