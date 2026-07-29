"""
Unified LLM Service.

Routes visual and text-based extraction queries to either
Google Gemini or OpenAI GPT models based on configuration settings.
"""

from __future__ import annotations

import json
import logging
import os
import requests

from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.llm.gemini_service import GeminiService

logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    """
    Unified LLM wrapper supporting multiple providers (Gemini and OpenAI).
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Initializing Unified LLM Service."
        )

        self.provider = (settings.llm_provider or "gemini").lower()
        self.gemini = GeminiService()

        self.openai_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        self.openai_model = settings.openai_model or "gpt-4.1-mini"
        self.temperature = 0.0
        self.max_tokens = 4096

    # ==========================================================
    # Ready Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Check if the active provider client settings are ready.
        """
        if self.provider == "openai":
            return bool(self.openai_key)
        return self.gemini.is_ready()

    # ==========================================================
    # Model Information
    # ==========================================================

    def model_info(
        self,
    ) -> dict:
        """
        Return active model details.
        """
        if self.provider == "openai":
            return {
                "provider": "OpenAI",
                "model": self.openai_model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        return self.gemini.model_info()

    # ==========================================================
    # Supported Fields
    # ==========================================================

    def supported_fields(
        self,
    ) -> list[str]:
        """
        Fields expected from LLM.
        """
        return self.gemini.supported_fields()

    # ==========================================================
    # Empty Record
    # ==========================================================

    def empty_record(
        self,
    ) -> dict:
        """
        Empty extraction result matching the comprehensive schema.
        """
        return self.gemini.empty_record()

    def schema_text(
        self,
    ) -> str:
        """
        JSON schema as formatted text.
        """
        return self.gemini.schema_text()

    # ==========================================================
    # Vision Completion (Direct Scrape)
    # ==========================================================

    def vision_completion(
        self,
        base64_image: str,
        ocr_text: str = "",
    ) -> str:
        """
        Send base64 image directly to active LLM API and return structured JSON.
        """
        if self.provider == "openai":
            logger.info(
                "Calling OpenAI API directly for vision extraction."
            )

            url = "https://api.openai.com/v1/chat/completions"

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
                "9. DATES & TIMES FORMATTING: Format all date and time fields (including \"auction_start_date_time\", \"auction_end_date_time\", \"submit_application\", \"inspection_schedule_from\", \"inspection_schedule_to\", \"repo_date\", \"catalogue_view_date\") strictly in standard format \"DD-MM-YYYY HH:MM\" or \"DD-MM-YYYY\" if no time is available.\n"
                "10. PER-AUCTION ACCOUNT DETAILS: Notice images typically list separate \"ACCOUNT DETAILS\" (Bank, Account No, IFSC Code) for each individual property/asset block. Extract these specifically inside each object in the \"auctions\" array (under \"emd_bank_name\", \"emd_account_no\", and \"emd_ifsc\").\n"
                "11. AUCTION DESCRIPTION (CRITICAL): The \"auction_description\" MUST be the exact, verbatim property description paragraph/list. You must copy the text word-for-word, preserving all original survey numbers, patta numbers, boundary plots, boundaries (East, West, North, South), areas, layout names, and addresses exactly as they appear in the image for that specific item. Absolutely no summarization, truncation, consolidation, or omission of any boundary/area details is permitted. Ensure the entire paragraph/list is extracted in full. Note that the OCR helper text is jumbled horizontally across columns; you MUST read the columns and boundaries visually from the image to reconstruct the correct boundaries and keep them with their respective properties.\n"
                "12. VISUAL DIGIT GUARDRAILS & PRINT ARTIFACT CONTROLS (CRITICAL): Newspaper print quality is often poor with dot-matrix text, low ink, or scanning noise. You MUST cross-validate shapes of digits carefully. Check for high-risk transpositions: `8` vs `3` or `0`, and `5` vs `6`. Look at neighboring lines, column totals, or contextual hints to resolve digits correctly. Never swap or corrupt phone/officer digits. DO NOT swap or rotate the values of reserve_price and emd_amount. The reserve_price is the asset's reserve price (usually a mid-size number per item, e.g. 6,078,500), and emd_amount is the Earnest Money Deposit (usually exactly 10% of the reserve_price, e.g. 6,07,850). If a single table row or section lists multiple reserve prices and EMDs for different properties (e.g. 3,05,04,500 and 4,24,69,000 written stacked or line-by-line), you MUST split them and extract each property as a separate auction object in the 'auctions' array with its respective correct reserve price and EMD. Never omit any reserve price listed in the table. Inspect column headers in the image visually to confirm which value belongs to which field.\n"
                "13. EXACT MATCHING FOR OTHER FIELDS: For fields like \"auction_no\" (which is strictly the row serial number or item index like \"01\", \"02\", \"03\" or \"Lot 1\"), \"asset_id\" (which is the platform-assigned asset ID number like \"4118\"), \"auction_id\" (which is the platform-assigned auction ID number like \"3887\"), \"property_address\"/\"assets_location\", contact details, and bank names, extract the exact values as printed in the notice without alterations, summary, or additions. Do not map Auction ID or Asset ID into Auction No. If the bid increment price (\"increment_price\" / \"bid_increment\") is not explicitly printed in the notice, you MUST calculate a fallback value based on the reserve price: if the reserve price is under 10 Lakhs (1,000,000), default to \"10000\"; if between 10 Lakhs and 50 Lakhs (5,000,000), default to \"25000\"; if above 50 Lakhs, default to \"50000\".\n"
                "14. INSPECTION SCHEDULE DATES: Visually scan the entire notice page (especially the lower sections, footnotes, terms and conditions, or small text paragraphs at the bottom) for terms like 'inspection', 'inspected', 'inspecting', 'date of inspection', or 'inspection of assets'. If an inspection date or range is printed anywhere in the notice (e.g. 'can be inspected on 24.07.2026' or 'inspection date: 2026-07-24'), you MUST extract the start date into 'inspection_schedule_from' and end date into 'inspection_schedule_to' (format YYYY-MM-DD). If only a single date is printed, assign it to both 'inspection_schedule_from' and 'inspection_schedule_to'. If there is absolutely no inspection date mentioned in the notice, you MUST look for the issue date / notice date printed at the very bottom left/right of the notice (usually next to 'Place', e.g., 'Date: 22.06.2026') and use that date as the fallback for both 'inspection_schedule_from' and 'inspection_schedule_to'. Never leave them blank.\n"
                "15. POSSESSION TYPE: Extract the possession status/type of the property (such as \"PHYSICAL\", \"SYMBOLIC\", \"CONSTRUCTIVE\"). Normalise to standard uppercase values: \"PHYSICAL\", \"SYMBOLIC\", or \"CONSTRUCTIVE\".\n"
                "18. INDIAN NUMERICAL GROUPING: Indian notices format numbers using a Lakh/Crore commas structure (e.g. \"4,93,50,000\"). This represents 8 digits \"49350000\" (4.935 Crores). You MUST be extremely careful: strip all formatting commas before parsing digits to prevent digit length multiplication. Never extract \"4,93,50,000\" as \"493500000\" (which is 9 digits, a 10x error). Grouping commas are format only; count digits visually.\n"
                "19. PER-AUCTION CONTACT AND OFFICER DETAILS: Document tables often contain branch-specific or row-specific contact numbers, mobile numbers, or names (e.g. \"Mob: [Mobile Number]\" or \"Phone: [Landline Number]\"). You MUST extract these specific numbers under the \"authorized_officer_number\" field inside the corresponding auction object in the \"auctions\" list. If an officer name or branch contact person name is also listed for that specific row/asset, extract it under \"authorized_officer_name\" inside the corresponding auction object. Only if no row-specific/branch contact detail is present, should they fall back to the notice-wide/zonal contact details. Extract all mobile/phone numbers found in the notice (such as at the bottom of the notice) and format them as a slash-separated string in \"authorized_officer_number\" if no specific officer number is listed.\n"
                "20. PAN-INDIAN MULTILINGUAL NOTICE TRANSLATION & TRANSLITERATION: Bank notices are frequently written in regional languages (Tamil, Hindi, Marathi, Telugu, Kannada, Gujarati, Bengali, Malayalam, Punjabi, etc.). You MUST visually read the regional language text, translate all semantic values (such as asset type, categories, dates, and descriptions) into English, and transliterate proper nouns (such as borrower/guarantor names, branch names, and location names) into English spelling. All output fields in the JSON payload must be populated strictly in English.\n\n"
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
                "model": self.openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_instruction
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "response_format": {
                    "type": "json_object"
                },
                "temperature": 0.0,
                "max_tokens": 4096
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}"
            }

            max_retries = 3
            for attempt in range(max_retries + 1):
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=60)
                    if response.status_code == 429 and attempt < max_retries:
                        logger.warning("OpenAI API rate limit hit (429). Retrying in 10 seconds...")
                        import time
                        time.sleep(10)
                        continue
                    if response.status_code != 200:
                        logger.error("OpenAI API request failed: %d - %s", response.status_code, response.text)
                        raise RuntimeError(f"OpenAI API returned error status {response.status_code}: {response.text}")
                    break
                except requests.exceptions.RequestException as exc:
                    if attempt < max_retries:
                        logger.warning("OpenAI network request failed: %s. Retrying in 5 seconds...", exc)
                        import time
                        time.sleep(5)
                        continue
                    raise exc

            try:
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                logger.info("OpenAI vision response received.")
                return content
            except Exception as exc:
                logger.exception("OpenAI API response parsing failed.")
                raise RuntimeError(f"OpenAI Parse Error : {exc}") from exc

        return self.gemini.vision_completion(base64_image, ocr_text)

    def targeted_reextraction(
        self,
        base64_image: str,
        missing_fields: list[str],
        ocr_text: str = "",
    ) -> dict:
        """
        Perform a targeted second pass LLM call focusing strictly on missing mandatory fields.
        """
        return self.gemini.targeted_reextraction(base64_image, missing_fields, ocr_text=ocr_text)

    # ==========================================================
    # Text-Based Extraction
    # ==========================================================

    def extract(
        self,
        text: str,
    ) -> dict:
        """
        Extract structured data from text using active LLM.
        """
        if self.provider == "openai":
            logger.info("Calling OpenAI API for text-based extraction.")
            url = "https://api.openai.com/v1/chat/completions"

            system_instruction = (
                "You are a highly defensive, zero-tolerance data-extraction text pipeline specialized in structural document intelligence. "
                "You process Indian bank auction notices. Your primary directive is 100% data fidelity. You must never invent, assume, approximate, or hallucinate any data point.\n\n"
                "### CRITICAL EXTRACTION PRINCIPLES:\n"
                "1. NO LOCAL OCR REFERENCE: Strictly extract directly and exclusively from the text content provided. Do not invent or infer characters.\n"
                "2. POSSESSION TYPE NORMALIZATION: Normalize possession status strictly to uppercase: \"PHYSICAL\", \"SYMBOLIC\", or \"CONSTRUCTIVE\".\n"
                "3. PAN-INDIAN LANGUAGE SUPPORT: Translate and transliterate regional Indian languages (Hindi, Marathi, Tamil, Telugu, Kannada, Gujarati, Bengali, etc.) strictly into English names, terms, and values.\n\n"
                "Output exclusively RAW, VALID JSON text matching the schema format below.\n"
                "DO NOT wrap the output payload inside markdown fences or code blocks. The output stream must start exactly with '{' and end with '}'."
            )

            prompt = (
                f"Extract all verified document data points exactly into the provided comprehensive JSON schema structure from the text below.\n\n"
                f"<text>\n{text}\n</text>\n\n"
                f"{self.schema_text()}"
            )

            payload = {
                "model": self.openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_instruction
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {
                    "type": "json_object"
                },
                "temperature": 0.0
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}"
            }

            max_retries = 3
            for attempt in range(max_retries + 1):
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=60)
                    if response.status_code == 429 and attempt < max_retries:
                        logger.warning("OpenAI API rate limit hit (429). Retrying in 10 seconds...")
                        import time
                        time.sleep(10)
                        continue
                    if response.status_code != 200:
                        logger.error("OpenAI API request failed: %d - %s", response.status_code, response.text)
                        raise RuntimeError(f"OpenAI API returned error status {response.status_code}: {response.text}")
                    break
                except requests.exceptions.RequestException as exc:
                    if attempt < max_retries:
                        logger.warning("OpenAI network request failed: %s. Retrying in 5 seconds...", exc)
                        import time
                        time.sleep(5)
                        continue
                    raise exc

            try:
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                return self.parse_json(content)
            except Exception as exc:
                logger.exception("OpenAI API text response parsing failed.")
                raise RuntimeError(f"OpenAI Parse Error : {exc}") from exc

        return self.gemini.extract(text)

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
        return self.gemini.parse_json(response)

    def close(
        self,
    ) -> None:
        self.gemini.close()
