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
            "bank_name",
            "branch_name",
            
            # Auction Mechanics and Dates
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

            # EMD and Payment Details
            "emd_bank_name",
            "emd_account_no",
            "emd_ifsc",
            "payment_type",

            # Portal Specific Fields
            "digital_certificate",
            "are_you_interested",
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
            "dues_amount",
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
                "bank_name": "",
                "branch_name": ""
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
                "are_you_interested": "",
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
                    "dues_amount": "",
                    "property_address": "",
                    "district": "",
                    "state": "",
                    "pin_code": "",
                    "emd_bank_name": "",
                    "emd_account_no": "",
                    "emd_ifsc": "",
                    "authorized_officer_name": "",
                    "authorized_officer_number": ""
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
            "4. LITERAL GEOGRAPHIC PARSING: Capture the complete, exact boundary or location text inside the \"property_address\" field. From that text block, cleanly isolate the standalone 6-digit pin code, the target district, and the state into their dedicated individual fields.\n\n"
            "### STRICT STANDARDIZATION & VALUE CONSTRAINTS:\n"
            "1. asset_type: Must be strictly one of: \"movable\", \"immovable\", or \"scrap\". Do not use any other words.\n"
            "2. asset_category: Must be strictly one of: \"scrap\", \"gold\", \"vehicle\", or \"property\".\n"
            "   - If asset_type is \"movable\", asset_category must be one of \"scrap\", \"gold\", or \"vehicle\".\n"
            "   - If asset_type is \"immovable\", asset_category must be \"property\".\n"
            "3. AUCTION TYPE: Extract the actual type of auction printed in the notice (such as \"E-Auction\", \"e-Auction\", \"online\", \"Public Auction\").\n"
            "4. AUTO EXTENSION: Must be strictly \"yes\" or \"no\". If not mentioned in the notice, default to \"\".\n"
            "5. AUTO EXTENSION MODE: Must be strictly \"infinite\" or \"custom\". If not mentioned, default to \"\".\n"
            "6. AUCTION LIVE STATUS: Must be strictly \"live\", \"reschedule\", \"cancel\", or \"Not Active\". If not mentioned, default to \"\".\n"
            "7. FIRST BID ACCEPTANCE CONDITION: Must be strictly \"yes\" or \"no\". If not mentioned, default to \"\".\n"
            "8. PAYMENT TYPE: Extract the raw payment mode/type printed in the notice (such as \"RTGS/ NEFT\", \"DD\", \"Demand Draft\", \"Cheque\").\n"
            "9. ARE YOU INTERESTED?: Must be strictly \"Yes\" or \"No\". If not mentioned, default to \"\".\n"
            "10. DATES & TIMES FORMATTING: Format all date and time fields (including \"auction_start_date_time\", \"auction_end_date_time\", \"submit_application\", \"inspection_schedule_from\", \"inspection_schedule_to\") strictly in standard format \"YYYY-MM-DD HH:MM:SS\" (e.g. \"2026-07-22 11:00:00\") or \"YYYY-MM-DD\" if no time is available. Carefully parse time ranges like \"11 AM to 1 PM\" into their respective start and end times (e.g. start: \"11:00:00\", end: \"13:00:00\"). If no time is printed in the notice, format as \"YYYY-MM-DD\" or use suffix \"00:00:00\" for datetime fields.\n"
            "11. PER-AUCTION ACCOUNT DETAILS: Notice images typically list separate \"ACCOUNT DETAILS\" (Bank, Account No, IFSC Code) for each individual property/asset block. Extract these specifically inside each object in the \"auctions\" array (under \"emd_bank_name\", \"emd_account_no\", and \"emd_ifsc\").\n"
            "12. AUCTION DESCRIPTION (CRITICAL): The \"auction_description\" MUST be the exact, verbatim property description paragraph/list. You must copy the text word-for-word, preserving all original survey numbers, patta numbers, boundary plots, boundaries (East, West, North, South), areas, layout names, and addresses exactly as they appear in the image for that specific item. Absolutely no summarization, truncation, consolidation, or omission of any boundary/area details is permitted. Ensure the entire paragraph/list is extracted in full. Note that the OCR helper text is jumbled horizontally across columns; you MUST read the columns and boundaries visually from the image to reconstruct the correct boundaries and keep them with their respective properties.\n"
            "13. IMAGE VS OCR PRIORITY (CRITICAL): The provided OCR helper text is rough and contains noise, typos, and character misreads (e.g. misreading digits or names). You MUST prioritize the raw visual text in the image. Double-check all numbers, digits, areas, and phone numbers directly against the image canvas before populating fields. Do not swap or corrupt phone digits. DO NOT swap or rotate the values of reserve_price, emd_amount, and dues_amount. The reserve_price is the asset's reserve price (usually a mid-size number per item, e.g. 6,078,500), emd_amount is the Earnest Money Deposit (usually exactly 10% of the reserve_price, e.g. 6,07,850), and dues_amount is the total outstanding dues of the borrower (usually a much larger notice-wide figure, e.g. 10,29,23,772.92). If a single table row or section lists multiple reserve prices and EMDs for different properties (e.g. 3,05,04,500 and 4,24,69,000 written stacked or line-by-line), you MUST split them and extract each property as a separate auction object in the 'auctions' array with its respective correct reserve price and EMD. Never omit any reserve price listed in the table. Inspect column headers in the image visually to confirm which value belongs to which field.\n"
            "14. EXACT MATCHING FOR OTHER FIELDS: For fields like \"auction_no\" (which is strictly the row serial number or item index like \"01\", \"02\", \"03\" or \"Lot 1\"), \"asset_id\" (which is the platform-assigned asset ID number like \"4118\"), \"auction_id\" (which is the platform-assigned auction ID number like \"3887\"), \"property_address\"/\"assets_location\", financial amounts, contact details, and bank names, extract the exact values as printed in the notice without alterations, summary, or additions. Do not map Auction ID or Asset ID into Auction No. If the bid increment price (\"increment_price\" / \"bid_increment\") is not explicitly printed in the notice, you MUST calculate a fallback value based on the reserve price: if the reserve price is under 10 Lakhs (1,000,000), default to \"10000\"; if between 10 Lakhs and 50 Lakhs (5,000,000), default to \"25000\"; if above 50 Lakhs, default to \"50000\".\n"
            "15. INSPECTION SCHEDULE DATES: Visually scan the entire notice page (especially the lower sections, footnotes, terms and conditions, or small text paragraphs at the bottom) for terms like 'inspection', 'inspected', 'inspecting', 'date of inspection', or 'inspection of assets'. If an inspection date or range is printed anywhere in the notice (e.g. 'can be inspected on 24.07.2026' or 'inspection date: 2026-07-24'), you MUST extract the start date into 'inspection_schedule_from' and end date into 'inspection_schedule_to' (format YYYY-MM-DD). If only a single date is printed, assign it to both 'inspection_schedule_from' and 'inspection_schedule_to'. If there is absolutely no inspection date mentioned in the notice, you MUST look for the issue date / notice date printed at the very bottom left/right of the notice (usually next to 'Place', e.g., 'Date: 22.06.2026') and use that date as the fallback for both 'inspection_schedule_from' and 'inspection_schedule_to'. Never leave them blank.\n"
            "16. DUES AMOUNT: Extract the outstanding dues liability amount printed on the notice (e.g. from labels like \"Total Dues\", \"Total Liabilities\", \"Total Dues Excluding Interest\", \"Dues Outstanding\"). Clean it of character noise (commas, spaces, Rs, \u20b9) and return it as a numeric digit string (e.g. \"Rs. 79,49,434.06/-\" must be returned as \"7949434.06\").\n"
            "17. POSSESSION TYPE: Extract the possession status/type of the property (such as \"PHYSICAL\", \"SYMBOLIC\", \"CONSTRUCTIVE\").\n"
            "18. INDIAN NUMERICAL GROUPING: Indian notices format numbers using a Lakh/Crore commas structure (e.g. \"4,93,50,000\"). This represents 8 digits \"49350000\" (4.935 Crores). You MUST be extremely careful: strip all formatting commas before parsing digits to prevent digit length multiplication. Never extract \"4,93,50,000\" as \"493500000\" (which is 9 digits, a 10x error). Grouping commas are format only; count digits visually.\n"
            "19. PER-AUCTION CONTACT AND OFFICER DETAILS: Document tables often contain branch-specific or row-specific contact numbers, mobile numbers, or names (e.g. \"Mob: [Mobile Number]\" or \"Phone: [Landline Number]\"). You MUST extract these specific numbers under the \"authorized_officer_number\" field inside the corresponding auction object in the \"auctions\" list. If an officer name or branch contact person name is also listed for that specific row/asset, extract it under \"authorized_officer_name\" inside the corresponding auction object. Only if no row-specific/branch contact detail is present, should they fall back to the notice-wide/zonal contact details. Extract all mobile/phone numbers found in the notice (such as at the bottom of the notice) and format them as a slash-separated string in \"authorized_officer_number\" if no specific officer number is listed.\n"
            "20. TAMIL AND MULTILINGUAL NOTICE TRANSLATION & TRANSLITERATION: Some notices are written partially or completely in Tamil. You MUST visually read the Tamil text, translate all semantic values (such as asset type, categories, dates, and descriptions) into English, and transliterate proper nouns (such as borrower/guarantor names, branch names, and city/village names) into English character spelling. All output fields in the JSON payload must be populated strictly in English.\n\n"
            "### PIPELINE COMPLETION COMPLIANCE:\n"
            "- Output exclusively RAW, VALID JSON text matching the schema format below.\n"
            "- DO NOT wrap the output payload inside markdown fences or code blocks (Never use ```json or ```).\n"
            "- Absolutely no conversational text, execution summaries, notes, or natural language introductions are permitted. The output stream must start exactly with '{' and end with '}'."
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
            "You are a highly defensive, zero-tolerance data-extraction text pipeline specialized in structural document intelligence. "
            "You process Indian bank auction notices. Your primary directive is 100% data fidelity. You must never invent, assume, approximate, or hallucinate any data point.\n\n"
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
