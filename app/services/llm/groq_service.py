"""Groq API client."""

import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.prompt import (
    AUCTION_EXTRACTION_SYSTEM_PROMPT,
    AUCTION_EXTRACTION_USER_PROMPT,
)
from app.schemas.extraction import RegexExtraction
from app.services.llm.parser import LLMParser

logger = get_logger(__name__)


class GroqService:
    """Call Groq Chat Completion API."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.parser = LLMParser()

    async def extract_auction_data(
        self,
        ocr_text: str,
        regex_hints: RegexExtraction,
    ) -> dict[str, Any]:
        """Extract structured auction information from OCR text."""

        if not self.settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is missing.")
            return {}

        
        ocr_text = ocr_text[:12000]

        prompt = AUCTION_EXTRACTION_USER_PROMPT.format(
            ocr_text=ocr_text,
            regex_hints=regex_hints.model_dump_json(indent=2),
        )

        payload = {
            "model": self.settings.GROQ_MODEL,
            "temperature": 0,
            "max_tokens": 4096,
            "response_format": {
                "type": "json_object"
            },
            "messages": [
                {
                    "role": "system",
                    "content": AUCTION_EXTRACTION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        url = (
            f"{str(self.settings.GROQ_BASE_URL).rstrip('/')}"
            "/chat/completions"
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.GROQ_TIMEOUT_SECONDS
            ) as client:

                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

                print("=" * 100)
                print("HTTP STATUS")
                print(response.status_code)
                print("=" * 100)

                response.raise_for_status()

                data = response.json()

                print("=" * 100)
                print("FULL RESPONSE")
                print(json.dumps(data, indent=2))
                print("=" * 100)

                content = data["choices"][0]["message"]["content"]

                print("=" * 100)
                print("LLM CONTENT")
                print(content)
                print("=" * 100)

                parsed = self.parser.parse_json(content)

                print("=" * 100)
                print("PARSED JSON")
                print(json.dumps(parsed, indent=2))
                print("=" * 100)

                return parsed

        except httpx.HTTPStatusError as exc:
            logger.exception("Groq HTTP Error")
            print(exc.response.text)
            raise

        except Exception:
            logger.exception("Groq extraction failed")
            raise