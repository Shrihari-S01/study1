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
            "### CRITICAL MULTI-RECORD & STRUCTURAL PARSING RULES:\n"
            "1. MULTI-RECORD ENTRY BOUNDARY DETECTION (CRITICAL): First, scan the document to detect every independent auction entry. Look for structural boundary markers such as 'Sl.No.', 'Serial Number', 'Lot Number', 'Property Number', 'Item No.', '1.', '2.', '3.', '4.', '5.', '6.', or separate borrower blocks across all columns (left and right). Extract EVERY detected auction as an independent object inside the 'auctions' array. Do NOT merge adjacent or multi-column auction entries. For multi-entry public notices (e.g., LIC Housing Finance or Bank notices containing 6 properties/lots), you MUST return exactly as many objects in the 'auctions' array as there are independent auction entries (e.g. 6 objects for 6 lots).\n"
            "2. GLOBAL AUCTION METADATA CLASSIFICATION & PROPAGATION:\n"
            "   - Extract document-level metadata (E-Auction Website, Global Inspection Schedule, Last Date of Submission, Auction Start/End Date & Time, Public Notice Date/Catalogue View Date, Payment Instructions, Terms & Conditions) once into top-level JSON fields (such as 'event_and_institution_details', 'auction_mechanics_and_dates', 'emd_and_payment_details').\n"
            "   - Shared values (like Global Catalogue View Date or Global Auction Date) apply to all auction records unless a specific auction lot defines its own local value.\n"
            "3. CATALOGUE VIEW DATE LOGIC:\n"
            "   - Catalogue View Date represents the publication/issue date of the notice (NOT the auction date).\n"
            "   - Priority: 1. Explicit Catalogue View Date, 2. Public Notice Date, 3. Notice Date, 4. Date near Authorized Officer signature, 5. Footer 'Date' (e.g. 'Date: 30.06.2026' -> '30-06-2026').\n"
            "   - NEVER use Auction Start/End Date, Last Submission Date, Inspection Date, Demand Notice Date, or Possession Date for Catalogue View Date.\n"
            "4. INSPECTION SCHEDULE LOGIC:\n"
            "   - Populate inspection dates ('inspection_schedule_from', 'inspection_schedule_to') ONLY from explicit inspection sections (e.g. 'Date & Time of Inspection of Property Documents', 'Inspection of the Property', 'Site Visit', 'Viewing Date').\n"
            "   - If no explicit inspection section exists in the document, return empty string \"\" for inspection fields.\n"
            "5. EMD BANK LOGIC ('emd_bank_name'):\n"
            "   - Search ONLY inside payment instruction sections ('EMD', 'Account Name', 'Account Number', 'IFSC', 'NEFT/RTGS', 'Beneficiary', 'Beneficiary Bank'). If missing, return empty string \"\"."
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
    # Targeted Re-extraction (Focus on 4 Key Fields)
    # ==========================================================

    def targeted_reextraction(
        self,
        base64_image: str,
        missing_fields: list[str],
        ocr_text: str = "",
    ) -> dict:
        """
        Perform a targeted second pass Gemini call focusing ONLY on missing mandatory fields.
        """
        logger.info("Running targeted Gemini re-extraction pass for missing fields: %s", missing_fields)

        field_descriptions = []
        if "emd_bank_name" in missing_fields:
            field_descriptions.append("- EMD Bank Name (emd_bank_name): Search ONLY inside payment instructions (Account Name, Account Number, IFSC, NEFT/RTGS, Beneficiary Bank). Do NOT use lending bank/seller bank unless specified in payment section.")
        if "catalogue_view_date" in missing_fields:
            field_descriptions.append("- Catalogue View Date (catalogue_view_date): Extract explicit Catalogue View Date, Notice Date, Publication Date, Dated/Date, or Place+Date. Format 'DD-MM-YYYY'. NEVER use Auction Date or EMD Date.")
        if "inspection_schedule_from_date" in missing_fields or "inspection_schedule_from" in missing_fields:
            field_descriptions.append("- Inspection Schedule From Date (inspection_schedule_from_date): Extract start date ONLY if document explicitly contains 'Inspection', 'Property Inspection', 'Site Visit', 'Viewing Date', or 'Inspection Schedule'. Format 'DD-MM-YYYY'.")
        if "inspection_schedule_to_date" in missing_fields or "inspection_schedule_to" in missing_fields:
            field_descriptions.append("- Inspection Schedule To Date (inspection_schedule_to_date): Extract end date ONLY if document explicitly contains 'Inspection', 'Property Inspection', 'Site Visit', 'Viewing Date', or 'Inspection Schedule'. Format 'DD-MM-YYYY'.")

        prompt = (
            "Review the document image and text again. Focus exclusively on extracting ONLY these missing fields:\n"
            + "\n".join(field_descriptions) + "\n\n"
            "Do not return any other fields. If a field is absent in the document, return \"\".\n"
            "Return a raw JSON object with keys: emd_bank_name, catalogue_view_date, inspection_schedule_from_date, inspection_schedule_to_date."
        )

        if ocr_text:
            prompt += f"\n\nOCR Reference Text:\n<ocr_text>\n{ocr_text}\n</ocr_text>"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
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
                "maxOutputTokens": 1024
            }
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                res_data = response.json()
                candidates = res_data.get("candidates", [])
                if candidates:
                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if content_parts:
                        raw_text = content_parts[0].get("text", "")
                        return self.parse_json(raw_text)
        except Exception as exc:
            logger.warning("Targeted re-extraction request failed: %s", exc)

        return {}

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
            # Fall back to robust json_repair if available
            try:
                import json_repair
                repaired = json_repair.repair_json(clean_res, return_objects=True)
                if isinstance(repaired, dict):
                    return repaired
            except ImportError:
                logger.warning("json_repair module not installed, skipping fallback repair.")
            except Exception as exc:
                logger.error("Failed to repair malformed JSON. Raw response: %s", clean_res)
                logger.exception("JSON repair failure.")
        
        return self.empty_record()

    def close(
        self,
    ) -> None:
        pass
