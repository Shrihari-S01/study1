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

        self.api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        self.model = settings.gemini_model or "gemini-1.5-flash"
        self.temperature = 0.0
        self.max_tokens = 4096

    def is_ready(
        self,
    ) -> bool:
        """
        Check Gemini client settings.
        """
        return bool(self.api_key)

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
                    "demand_notice_date": "",
                    "symbolic_possession_date": "",
                    "total_closure_amount": "",
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
            "0. IN-DEPTH MULTI-COLUMN & MULTI-AUCTION SCANNING (CRITICAL):\n"
            "   - Perform an exhaustive, pixel-by-pixel spatial analysis across all columns (left, middle, right) from top to bottom.\n"
            "   - Detect and count EVERY individual auction lot or serial number block (e.g. Sl.No.1, Sl.No.2, Sl.No.3, Sl.No.4, Sl.No.5, Sl.No.6, ... up to 20+ auctions).\n"
            "   - If the notice image contains 6 auctions, you MUST generate exactly 6 auction objects inside the 'auctions' array.\n"
            "   - For EVERY detected auction block, extract ALL visually present fields (borrower_name, loan_account_number, reserve_price, emd_amount, auction_description, property_address, possession_type, asset_type='immovable', asset_category='property', emd_bank_name, emd_account_no, emd_ifsc, authorized_officer_number).\n"
            "   - NEVER skip, truncate, or return dummy/empty objects for valid auction blocks printed in the image.\n\n"
            "1. STRICT ASSET CATEGORY & ASSET TYPE CONSTRAINTS:\n"
            "   - asset_type: Must be strictly 'immovable' or 'movable'. For any flat, house, plot, land, shop, building, or residential/commercial real estate, set asset_type strictly to 'immovable'.\n"
            "   - asset_category: Must be strictly one of: 'scrap', 'gold', 'vehicle', 'pearl', or 'property'. For ALL real estate, flats, houses, lands, plots, shops, buildings, or residential/commercial properties, asset_category MUST be strictly 'property'. NEVER output 'residential', 'flat', 'land', or 'house' as asset_category.\n\n"
            "2. FOUR-CORNER CATALOGUE VIEW DATE SCANNING (CRITICAL):\n"
            "   - Scan all four corners of the image document (top-left, top-right, bottom-left, bottom-right corners, header lines, and footer signature blocks next to Place/Authorized Officer).\n"
            "   - Any standalone date printed with label 'Date:', 'DATE:', 'Dated:', 'DATED:', 'Date :', 'DATE :' (without conflicting prefixes like 'Auction Date', 'Inspection Date', 'EMD Date', 'Demand Notice Date', 'Possession Date') MUST be extracted into top-level 'catalogue_view_date' in standard 'DD-MM-YYYY' format (e.g. 'Date: 30.06.2026' -> '30-06-2026').\n"
            "   - This document publication date applies globally to all auction records in the notice.\n\n"
            "3. GLOBAL AUCTION METADATA CLASSIFICATION & PROPAGATION:\n"
            "   - Extract document-level metadata (E-Auction Website, Global Inspection Schedule, Last Date of Submission, Auction Start/End Date & Time, Public Notice Date/Catalogue View Date, Payment Instructions, Terms & Conditions) once into top-level JSON fields.\n"
            "   - Shared values apply to all auction records unless a specific auction lot defines its own local value.\n\n"
            "4. INSPECTION SCHEDULE LOGIC (IMAGE NOTICES):\n"
            "   - Populate 'inspection_schedule_from' and 'inspection_schedule_to' ONLY if an explicit inspection label exists in text.\n"
            "   - Accepted labels: 'Inspection', 'Inspection Date', 'Inspection Schedule', 'Date & Time of Inspection', 'Property Inspection', 'Site Visit', 'Viewing Date'.\n"
            "5. EMD BANK LOGIC ('emd_bank_name'):\n"
            "   - Extract explicit Beneficiary Bank / Bank field under Account Details / Payment section (e.g. Beneficiary Bank: Axis Bank -> emd_bank_name = 'Axis Bank').\n"
            "6. COMPREHENSIVE BORROWER & MULTI-PARTY EXTRACTION (CRITICAL):\n"
            "   - Extract ONLY the legal entity or person names of borrowers, co-borrowers, guarantors, legal heirs, and joint account holders into borrower_name (optionally formatted as 'Company Name (Prop. Person Name)' if a proprietor is listed).\n"
            "   - STOP borrower_name extraction at any address indicators (such as 'having registered office/address', 'address at', 'r/o', 'residing at', 'situated at', 'village', 'plot no', 'door no', 'survey no', 'street', 'road', 'district', 'state', 'PIN').\n"
            "   - NEVER include borrower addresses inside borrower_name. Any address text following a borrower MUST be placed into property_address or asset_location."
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
                if any(x in exc_str for x in ["getaddrinfo", "name resolution", "connection refused", "failed to resolve"]):
                    logger.error("Critical network connection failure: %s. Aborting retries.", exc)
                    raise exc
                if attempt < max_retries:
                    logger.warning("Network request attempt %d/%d failed: %s. Retrying in 5 seconds...", attempt + 1, max_retries + 1, exc)
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

    def targeted_reextraction(
        self,
        base64_image: str,
        missing_fields: list[str] | None = None,
        ocr_text: str = "",
        common_missing: list[str] | None = None,
        auctions_missing: list[dict] | None = None,
    ) -> dict:
        """
        Perform a targeted second pass Gemini call focusing strictly on missing fields per auction object.
        """
        if missing_fields and not common_missing:
            common_missing = missing_fields

        common_missing = common_missing or []
        auctions_missing = auctions_missing or []

        if not common_missing and not auctions_missing:
            return {}

        logger.info(
            "Running targeted Gemini per-object re-extraction pass. Common missing: %s, Auction objects missing: %s",
            common_missing, len(auctions_missing)
        )

        request_details = {}
        if common_missing:
            request_details["common_missing_fields"] = common_missing
        if auctions_missing:
            request_details["auctions_missing_fields"] = auctions_missing

        prompt = (
            "Review the document image and OCR text again to locate missing values for the following targeted fields:\n\n"
            f"{json.dumps(request_details, indent=2)}\n\n"
            "CRITICAL RE-EXTRACTION RULES:\n"
            "1. SPATIAL OBJECT ISOLATION: For each requested auction object (identified by 'auction_no'), re-examine its specific spatial section on the image. Extract missing values ONLY from within that auction object's space.\n"
            "2. NO BLEEDING: Do NOT copy values from adjacent rows or neighbor objects. If a field is absent, set value to \"\".\n"
            "3. RETURN FORMAT: Output a raw JSON object containing:\n"
            "{\n"
            '  "common_fields": { "field_name": "extracted_value" },\n'
            '  "auctions": [\n'
            '     { "auction_no": "1", "field_name": "extracted_value" },\n'
            '     { "auction_no": "2", "field_name": "extracted_value" }\n'
            "  ]\n"
            "}"
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
                "maxOutputTokens": 2048
            }
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
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

    def extract_pdf_catalogue(
        self,
        pdf_text: str,
    ) -> dict:
        """
        Extract structured data from PDF auction catalogue text using Section-aware Label-based prompt.
        Pipeline B: Dedicated for PDF catalogues. Does not affect image pipeline.
        """
        logger.info("Calling Gemini API for Pipeline B (PDF Catalogue Text Extraction).")

        system_instruction = (
    "You are an enterprise-grade Auction Catalogue PDF Extraction Engine. "
    "Your responsibility is to extract structured auction data from complete multi-page PDF catalogues with 99% accuracy. "
    "Never hallucinate, never guess, and never overwrite correctly extracted values.\n\n"

    "=========================\n"
    "STAGE 1 - DOCUMENT UNDERSTANDING\n"
    "=========================\n"
    "1. Read the ENTIRE PDF before extracting any fields.\n"
    "2. Merge all pages into one logical document.\n"
    "3. Build these document sections:\n"
    "- Auction Header\n"
    "- Seller Details\n"
    "- Seller Account Details / Beneficiary Details / Payment Details\n"
    "- Officer Details\n"
    "- Lot Details\n"
    "- Terms & Conditions\n"
    "- Annexure\n"
    "Never extract fields directly from random pages.\n\n"

    "=========================\n"
    "STAGE 2 - HEADER EXTRACTION\n"
    "=========================\n"
    "Extract only once:\n"
    "- auction_identifier\n"
    "- auction_no\n"
    "- catalogue_view_date\n"
    "- inspection_schedule\n"
    "- auction_date_time\n"
    "- auction_end_date_time\n"
    "- institution_seller\n"
    "- auction_office\n"
    "- emd_bank_name\n"
    "- emd_account_number\n"
    "- emd_ifsc\n"
    "- emd_branch\n"
    "- auction_department\n"
    "- authorized_officer_name\n"
    "- authorized_officer_number\n"
    "Propagate these values to every lot.\n\n"

    "=========================\n"
    "STAGE 3 - LOT DETECTION\n"
    "=========================\n"
    "Every occurrence of:\n"
    "- Lot No\n"
    "- Lot No -\n"
    "- Lot Number\n"
    "- Item No\n"
    "starts a NEW auction object.\n"
    "Never merge multiple lots into one object.\n"
    "Output one JSON object for every detected lot.\n\n"

    "=========================\n"
    "STAGE 4 - LOT FIELD MAPPING\n"
    "=========================\n"
    "For every lot extract:\n"
    "- lot_no\n"
    "- lot_name\n"
    "- product_type\n"
    "- category\n"
    "- quantity\n"
    "- unit\n"
    "- lot_location\n"
    "- state\n"
    "- start_price\n"
    "- bid_increment\n"
    "- gst\n"
    "- tcs\n"
    "- bid_valid_till\n\n"

    "Map:\n"
    "Lot Name -> auction_description\n"
    "Start Price in INR -> reserve_price\n"
    "Bid Increment in INR -> increment_price\n"
    "Lot Location -> assets_location\n\n"

    "Never replace extracted numeric values with 0 or null.\n\n"

    "=========================\n"
    "STAGE 5 - AUCTION NUMBER\n"
    "=========================\n"
    "Example:\n"
    "MSTC/SRO/.../19530\n\n"
    "auction_identifier = full string\n"
    "auction_no = 19530\n\n"
    "Never store company names inside auction_no.\n\n"

    "=========================\n"
    "STAGE 6 - ASSET CLASSIFICATION\n"
    "=========================\n"
    "Determine asset category from the CURRENT LOT only.\n"
    "Never infer category from document header.\n"
    "Never return 'TO BE' when Category exists.\n\n"

    "Examples:\n"
    "Iron and Steel -> Iron and Steel\n"
    "Battery -> Battery\n"
    "Plastic -> Plastic\n"
    "Rubber -> Rubber\n"
    "Electrical Items -> Electrical\n"
    "Vehicle -> Vehicle\n"
    "Gold -> Gold\n"
    "Property -> Property\n\n"

    "asset_type:\n"
    "Movable for scrap, machinery, vehicle, battery, metal.\n"
    "Immovable only for land, plot, building, house.\n\n"

    "=========================\n"
    "STAGE 7 - UNIVERSAL BANK EXTRACTION\n"
    "=========================\n"
    "Search these sections:\n"
    "Seller Account Details\n"
    "Beneficiary Details\n"
    "Payment Details\n"
    "Bank Details\n"
    "Account Details\n"
    "EMD Details\n\n"

    "Map:\n"
    "Beneficiary Name -> institution_seller\n"
    "Bank Name -> emd_bank_name\n"
    "Branch -> emd_branch + auction_department\n"
    "A/c No -> emd_account_number\n"
    "Account Number -> emd_account_number\n"
    "IFSC -> emd_ifsc\n"
    "IFS Code -> emd_ifsc\n\n"

    "Validation:\n"
    "Bank Name must be a bank.\n"
    "Account Number must contain only digits.\n"
    "IFSC must match Indian IFSC format.\n"
    "Reject instructional paragraphs.\n\n"

    "=========================\n"
    "STAGE 8 - SELLER & OFFICER\n"
    "=========================\n"
    "Seller Name -> institution_seller\n"
    "Seller Address -> auction_office\n\n"

    "Authorized Officer priority:\n"
    "Authorized Officer\n"
    "Authorized Signatory\n"
    "Authorized Representative\n"
    "If none exist, use Contact Person.\n"
    "Never use MSTC Helpdesk.\n\n"

    "=========================\n"
    "STAGE 9 - VALIDATION\n"
    "=========================\n"
    "Validate before output:\n"
    "Detected Lots == Output Records\n"
    "auction_no must be numeric\n"
    "reserve_price > 0 if Start Price exists\n"
    "increment_price must equal Bid Increment\n"
    "assets_location must equal Lot Location\n"
    "asset_category must not be 'TO BE' if Category exists\n"
    "auction_description must equal Lot Name\n"
    "EMD bank fields must pass validation.\n\n"

    "=========================\n"
    "STAGE 10 - HALLUCINATION PREVENTION\n"
    "=========================\n"
    "Never infer missing values.\n"
    "Never fabricate bank details.\n"
    "Never fabricate prices.\n"
    "Never fabricate auction numbers.\n"
    "Never overwrite regex-extracted values.\n"
    "If a value is not explicitly present, return null.\n\n"

    "Return ONLY valid JSON exactly matching the required schema."
)
        import sys
        import json as json_lib
        def safe_print(text: str):
            try:
                sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
            except Exception:
                pass

        safe_print("\n========== FIRST 2000 CHARS OF PDF_TEXT ==========")
        safe_print(pdf_text[:2000] if pdf_text else "[Empty PDF Text]")
        safe_print("===================================================\n")

        prompt = (
            f"Extract all verified PDF auction catalogue data points exactly into the provided JSON schema structure from the text below.\n\n"
            f"<pdf_text>\n{pdf_text}\n</pdf_text>\n\n"
            f"{self.schema_text()}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": f"{system_instruction}\n\n{prompt}"}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
                "maxOutputTokens": 8192
            }
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=45)
            if response.status_code == 200:
                res_data = response.json()
                candidates = res_data.get("candidates", [])
                if candidates:
                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if content_parts:
                        raw_text = content_parts[0].get("text", "")
                        safe_print("\n========== RAW LLM RESPONSE (EXTRACT_PDF_CATALOGUE) ==========")
                        safe_print(raw_text)
                        safe_print("================================================================\n")
                        parsed = self.parse_json(raw_text)
                        safe_print("\n========== PARSED JSON OBJECT FROM RAW LLM RESPONSE ==========")
                        safe_print(json_lib.dumps(parsed, indent=2))
                        safe_print("================================================================\n")
                        return parsed
            else:
                logger.error("Gemini API HTTP Error %d: %s", response.status_code, response.text)
        except Exception as exc:
            logger.error("PDF catalogue extraction failed: %s", exc)

        return self.empty_record()

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
