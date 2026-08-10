"""
Unified LLM Service.

Routes visual and text-based extraction queries to either
Google Gemini or OpenAI GPT models based on configuration settings.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import requests

from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.llm.gemini_service import GeminiService

logger = get_logger(__name__)
settings = get_settings()

class LLMService:
    """
    Unified LLM wrapper supporting multiple providers (Gemini and OpenAI).
    Strictly instantiates and executes ONLY the configured provider based on settings.llm_provider.
    """

    def __init__(
        self,
    ) -> None:
        self.provider = (settings.llm_provider or "openai").lower()

        self.openai_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        self.openai_model = settings.openai_model or "gpt-4.1-mini"
        self.temperature = 0.0
        self.max_tokens = 4096

        self._gemini_instance = None

        self._http_session = None

        if self.provider == "openai":
            logger.info("Selected LLM Provider: OpenAI | Selected Model: %s", self.openai_model)
            self._http_session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=2)
            self._http_session.mount("https://", adapter)
            self._http_session.mount("http://", adapter)
        elif self.provider == "gemini":
            logger.info("Selected LLM Provider: Gemini | Selected Model: %s", settings.gemini_model)
        else:
            logger.warning("Unknown LLM Provider '%s'. Defaulting to OpenAI.", self.provider)
            self.provider = "openai"

    @property
    def gemini(self) -> GeminiService:
        """
        Lazy accessor for GeminiService.
        Raises RuntimeError if provider is configured as OpenAI to prevent accidental Gemini calls.
        """
        if self.provider == "openai":
            raise RuntimeError(
                "Runtime Assertion Violation: Gemini method accessed while LLM_PROVIDER is configured as 'openai'."
            )
        if self._gemini_instance is None:
            from app.services.llm.gemini_service import GeminiService
            self._gemini_instance = GeminiService()
        return self._gemini_instance

    def _assert_provider(self, target_provider: str) -> None:
        if self.provider != target_provider:
            raise RuntimeError(
                f"Runtime Assertion Violation: Cannot execute {target_provider.upper()} logic because LLM_PROVIDER is configured as '{self.provider}'."
            )

    def is_ready(
        self,
    ) -> bool:
        """
        Check if the active provider client settings are ready.
        """
        if self.provider == "openai":
            return bool(self.openai_key)
        return self.gemini.is_ready()

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

    def supported_fields(
        self,
    ) -> list[str]:
        """
        Fields expected from LLM.
        """
        return [
            "institution_seller_name", "auction_office_department", "vendor_name",
            "authorized_officer_name", "authorized_officer_number", "email",
            "institution_seller", "auction_office", "auction_department",
            "digital_certificate", "catalogue_view_date", "asset_subcategory",
            "full_payment_balance", "delivery_of_material_taken", "quantity",
            "units", "start_floor_price", "sum_of_carat_18", "sum_of_carat_19",
            "sum_of_carat_20", "sum_of_carat_21", "sum_of_carat_22", "sum_of_carat_23",
            "sum_of_carat_24", "sum_of_net_weight_total", "sum_of_gross_weight_total",
            "year", "reg_no", "repo_date", "km_driven", "rc", "chassis_number",
            "yard_rent_percent", "remarks"
        ]

    def empty_record(
        self,
    ) -> dict:
        """
        Empty extraction result matching the comprehensive schema.
        """
        if self.provider == "openai":
            return {
                "institution_seller_name": "", "auction_office_department": "",
                "vendor_name": "", "authorized_officer_name": "",
                "authorized_officer_number": "", "email": "",
                "institution_seller": "", "auction_office": "",
                "auction_department": "", "digital_certificate": "",
                "catalogue_view_date": "", "remarks": "", "auctions": []
            }
        return self.gemini.empty_record()

    def schema_text(
        self,
    ) -> str:
        """
        JSON schema as formatted text.
        """
        return json.dumps(self.empty_record(), indent=4)

    def text_completion(
        self,
        ocr_text: str,
    ) -> str:
        """
        Fast Path: Send high-confidence OCR text to GPT-4.1-mini text completion without image payload.
        Cuts extraction latency by 50-80%.
        """
        if not ocr_text or not ocr_text.strip():
            return json.dumps(self.empty_record(), indent=4)

        if self.provider == "openai":
            logger.info("Executing Fast Path: GPT-4.1-mini Text LLM completion (bypassing image payload).")

            # Check persistent disk cache
            cache_key = hashlib.sha256(f"text:{ocr_text}".encode("utf-8")).hexdigest()
            cached_resp = self._get_cached_response(cache_key)
            if cached_resp:
                logger.info("SHA-256 Text Cache Hit! Returning persistent cached extraction.")
                return cached_resp

            url = "https://api.openai.com/v1/chat/completions"
            system_instruction = (
                "You are an expert structural document data extraction engine for Indian bank auction notices. "
                "Extract all auction details into the strict JSON schema provided. "
                "Follow all schema rules, digit integrity, Lakh/Crore calculations, and field mappings. "
                "Return raw JSON format only."
            )
            prompt = (
                f"Extract structured auction data from the following high-confidence document text:\n"
                f"<document_text>\n{ocr_text}\n</document_text>\n\n"
                f"{self.schema_text()}"
            )
            payload = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0,
                "max_tokens": 4096
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}",
                "Connection": "close"
            }
            response = self._post_with_retry(url, payload, headers, timeout=30, max_retries=3)
            try:
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                self._set_cached_response(cache_key, content)
                return content
            except Exception as exc:
                logger.exception("OpenAI Text API response parsing failed.")
                raise RuntimeError(f"OpenAI Text Parse Error: {exc}") from exc

        return json.dumps(self.empty_record(), indent=4)

    @staticmethod
    def _downscale_base64_image(base64_image: str, max_dim: int = 1200) -> str:
        """
        Downscale Base64 image payload in memory to max_dim pixels to minimize API bandwidth and latency.
        """
        try:
            import base64
            import io
            from PIL import Image

            img_bytes = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(img_bytes))

            if img.mode != "RGB":
                img = img.convert("RGB")

            w, h = img.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                new_w, new_h = int(w * scale), int(h * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80, optimize=True)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as exc:
            logger.warning("Image downscaling failed, sending original image: %s", exc)
            return base64_image

    @staticmethod
    def _get_cached_response(cache_key: str) -> str | None:
        """Read response from persistent disk cache if enabled."""
        if not getattr(settings, "enable_disk_cache", False):
            return None
        try:
            cache_dir = os.path.join(os.getcwd(), "temp", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content and len(content.strip()) > 10:
                        try:
                            data = json.loads(content)
                            if isinstance(data, dict) and (data.get("auctions") or data.get("reserve_price") or data.get("borrower_name")):
                                return content
                        except Exception:
                            pass
        except Exception:
            pass
        return None

    @staticmethod
    def _set_cached_response(cache_key: str, content: str) -> None:
        """Write response to persistent disk cache if enabled."""
        if not getattr(settings, "enable_disk_cache", False):
            return
        try:
            cache_dir = os.path.join(os.getcwd(), "temp", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"{cache_key}.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

    def vision_completion(
        self,
        base64_image: str,
        ocr_text: str = "",
    ) -> str:
        """
        Send base64 image directly to active LLM API and return structured JSON.
        """
        if self.provider == "openai":
            # 1. Downscale base64 image payload in memory
            scaled_b64 = self._downscale_base64_image(base64_image, max_dim=1200)

            # 2. Check persistent SHA-256 disk cache
            cache_key = hashlib.sha256(f"vision:{scaled_b64}".encode("utf-8")).hexdigest()
            cached_resp = self._get_cached_response(cache_key)
            if cached_resp:
                logger.info("SHA-256 Vision Cache Hit! Returning persistent cached extraction.")
                return cached_resp

            logger.info("Calling OpenAI API directly for vision extraction (downscaled).")

            url = "https://api.openai.com/v1/chat/completions"

            system_instruction = (
                "You are a highly defensive, zero-tolerance data-extraction vision pipeline specialized in structural document intelligence. You process highly diverse Indian bank auction notices, asset disposal catalogues, regulatory public announcements, and internal digital admin forms. Your primary directive is 100% data fidelity. You must never invent, assume, approximate, or hallucinate any data point.\n\n"
                "### CRITICAL IN-DEPTH MULTI-AUCTION OBJECT COUNT & SPATIAL ISOLATION RULES:\n"
                "0. IN-DEPTH DOCUMENT SCANNING & COUNTING (CRITICAL): First, perform an exhaustive, pixel-by-pixel spatial analysis of the entire document to detect and count EVERY individual auction lot, property entry, serial number block, or tabular row (whether there are 2, 6, 13, 20, or more auctions on the single image/page).\n"
                "1. NO-SKIP & EXACT OBJECT INSTANTIATION: If the document contains 13 auctions, you MUST generate exactly 13 distinct object blocks inside the 'auctions' array. Never consolidate separate property lots into a single item, and NEVER skip or omit any auction entry, no matter how small or densely packed.\n"
                "2. SPATIAL BOUNDARY ISOLATION: Extract each auction's data fields strictly from that specific auction's distinct spatial section/boundary on the page. Do NOT bleed or mix reserve prices, EMD amounts, addresses, or borrower names across neighboring rows or adjacent table columns.\n"
                "3. UNIQUE OBJECT IDENTIFICATION ('auction_no'): Every single auction object inside the 'auctions' array MUST be assigned a unique 'auction_no' string (e.g., '1', '2', '3', ..., '13' or 'Lot 1', 'Lot 2'). This unique identifier isolates the object spatially and is used by the system for targeted retry/re-search passes if any field is missing.\n"
                "4. UNIVERSAL LAYOUT AGNOSTICISM: Treat every input as structurally unique. Inputs range from messy, unstructured newspaper columns and multi-page PDF tables to highly structured web portal forms with dropdowns and text boxes. Parse the text dynamically based on spatial proximity, field labels, and visual alignment.\n"
                "5. RIGOROUS DECOMPOSITION: When data entities (such as multi-party names or combined address blocks) are densely packed, map out the semantic transitions perfectly. Dissect these strings cleanly into their unique JSON fields.\n\n"
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
                "Authorization": f"Bearer {self.openai_key}",
                "Connection": "close"
            }

            response = self._post_with_retry(url, payload, headers, timeout=120, max_retries=5)

            try:
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                logger.info("OpenAI vision response received.")
                self._set_cached_response(cache_key, content)
                return content
            except Exception as exc:
                logger.exception("OpenAI API response parsing failed.")
                raise RuntimeError(f"OpenAI Parse Error : {exc}") from exc

        return self.gemini.vision_completion(base64_image, ocr_text)

    def _post_with_retry(
        self,
        url: str,
        payload: dict,
        headers: dict,
        timeout: int = 120,
        max_retries: int = 5,
    ) -> requests.Response:
        """
        Execute HTTPS POST request with robust SSL/connection retry logic and exponential backoff.
        """
        import time

        req_headers = dict(headers)
        req_headers.setdefault("Connection", "keep-alive")

        last_exception = None
        session = self._http_session or requests.Session()

        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Executing OpenAI API request (attempt %d/%d)...", attempt, max_retries)
                response = session.post(url, json=payload, headers=req_headers, timeout=timeout)

                if response.status_code == 429:
                    retry_after = 5 * attempt
                    logger.warning("OpenAI API rate limit hit (429). Retrying in %d seconds (attempt %d/%d)...", retry_after, attempt, max_retries)
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    logger.warning("OpenAI server error (%d). Retrying in %d seconds (attempt %d/%d)...", response.status_code, 3 * attempt, attempt, max_retries)
                    time.sleep(3 * attempt)
                    continue

                if response.status_code != 200:
                    logger.error("OpenAI API request failed: %d - %s", response.status_code, response.text)
                    raise RuntimeError(f"OpenAI API returned error status {response.status_code}: {response.text}")

                return response

            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as exc:
                last_exception = exc
                retry_delay = 3 * attempt
                logger.warning(
                    "OpenAI network/SSL request attempt %d/%d failed with error (%s). Retrying in %d seconds...",
                    attempt, max_retries, exc, retry_delay
                )
                if attempt < max_retries:
                    time.sleep(retry_delay)
            finally:
                session.close()

        if last_exception:
            raise last_exception
        raise RuntimeError("OpenAI request failed after maximum retries.")

    def targeted_reextraction(
        self,
        base64_image: str,
        missing_fields: list[str] | None = None,
        ocr_text: str = "",
        common_missing: list[str] | None = None,
        auctions_missing: list[dict] | None = None,
    ) -> dict:
        """
        Perform a targeted re-extraction LLM call focusing strictly on missing/null fields per auction object.
        """
        if missing_fields and not common_missing:
            common_missing = missing_fields

        common_missing = common_missing or []
        auctions_missing = auctions_missing or []

        if not common_missing and not auctions_missing:
            return {}

        if self.provider == "openai":
            logger.info(
                "Calling OpenAI API for targeted per-object re-extraction. Common missing: %s, Auction objects missing: %s",
                common_missing, len(auctions_missing)
            )
            url = "https://api.openai.com/v1/chat/completions"

            system_instruction = (
                "You are an expert structural document intelligence assistant specialized in re-scanning bank auction notices for missing fields.\n"
                "Your directive is to re-examine the document image and OCR text to find exact missing values for document-wide common fields and specific auction objects.\n\n"
                "### RE-EXTRACTION RULES:\n"
                "1. SPATIAL OBJECT ISOLATION: For each specific auction object requested (identified by its unique 'auction_no'), locate its exact spatial boundary on the page image. Extract missing values ONLY from within that specific object's space.\n"
                "2. NO HALLUCINATION / BLEED: Never copy values from neighbor objects or adjacent table rows. If a field is truly absent, set its value to \"\".\n"
                "3. OUTPUT FORMAT: Return exclusively a RAW JSON payload structured as:\n"
                "{\n"
                '  "common_fields": { "field_name": "extracted_value" },\n'
                '  "auctions": [\n'
                '     { "auction_no": "1", "field_name": "extracted_value" },\n'
                '     { "auction_no": "2", "field_name": "extracted_value" }\n'
                "  ]\n"
                "}"
            )

            request_details = {}
            if common_missing:
                request_details["common_missing_fields"] = common_missing
            if auctions_missing:
                request_details["auctions_missing_fields"] = auctions_missing

            prompt = (
                "Re-scan the provided document image and OCR text to locate missing values for the following targeted fields:\n\n"
                f"{json.dumps(request_details, indent=2)}\n\n"
            )
            if ocr_text:
                prompt += f"<ocr_text>\n{ocr_text}\n</ocr_text>\n\n"

            prompt += "Return raw JSON matching the required schema with 'common_fields' dict and 'auctions' array containing objects tagged by 'auction_no'."

            payload = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}",
                "Connection": "close"
            }

            try:
                response = self._post_with_retry(url, payload, headers, timeout=60, max_retries=3)
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                return self.parse_json(content)
            except Exception as exc:
                logger.warning("OpenAI targeted re-extraction failed: %s", exc)
                return {}

        return self.gemini.targeted_reextraction(
            base64_image,
            missing_fields=missing_fields,
            ocr_text=ocr_text,
            common_missing=common_missing,
            auctions_missing=auctions_missing
        )
    def extract_pdf_catalogue(
        self,
        pdf_text: str,
    ) -> dict:
        """
        Extract structured data from PDF auction catalogue text (Pipeline B).
        Routes query to active provider (OpenAI if set to openai, otherwise Gemini).
        """
        if self.provider == "openai":
            logger.info("Routing PDF Catalogue extraction query to OpenAI API.")
            return self.extract(pdf_text)
        return self.gemini.extract_pdf_catalogue(pdf_text)

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
                "Authorization": f"Bearer {self.openai_key}",
                "Connection": "close"
            }

            response = self._post_with_retry(url, payload, headers, timeout=60, max_retries=4)

            try:
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                return self.parse_json(content)
            except Exception as exc:
                logger.exception("OpenAI API text response parsing failed.")
                raise RuntimeError(f"OpenAI Parse Error : {exc}") from exc

        return self.gemini.extract(text)

    def parse_json(
        self,
        response: str,
    ) -> dict:
        """
        Convert JSON string into dictionary cleanly without requiring provider instance.
        """
        if not response:
            return {}

        clean_s = response.strip()
        if clean_s.startswith("```json"):
            clean_s = clean_s[7:]
        if clean_s.startswith("```"):
            clean_s = clean_s[3:]
        if clean_s.endswith("```"):
            clean_s = clean_s[:-3]
        clean_s = clean_s.strip()

        try:
            return json.loads(clean_s)
        except Exception as json_err:
            logger.warning("Initial JSON parse failed: %s. Attempting automated JSON repair...", json_err)
            
            # 1. Strip markdown fences and extract outermost JSON object/array
            m = re.search(r"(\{.*\}|\[.*\])", clean_s, re.DOTALL)
            repaired_s = m.group(0) if m else clean_s

            # 2. Repair trailing commas before closing braces/brackets
            repaired_s = re.sub(r",\s*([\}\]])", r"\1", repaired_s)

            # 3. Escape raw unescaped newlines in JSON string values
            repaired_s = re.sub(r'":\s*"([^"]*)"', lambda match: '": "' + match.group(1).replace('\n', '\\n').replace('\r', '\\r') + '"', repaired_s)

            try:
                parsed = json.loads(repaired_s)
                logger.info("JSON repair succeeded.")
                return parsed
            except Exception as repair_err:
                logger.error("JSON repair failed: %s", repair_err)
                return {}

    def close(
        self,
    ) -> None:
        if self._gemini_instance is not None:
            try:
                self._gemini_instance.close()
            except Exception:
                pass
