"""End-to-end auction notice processing pipeline."""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UploadStatus
from app.core.exceptions import NotFoundError, ProcessingError
from app.core.logger import get_logger
from app.models.auction import Auction
from app.repositories.auction_repository import AuctionRepository
from app.repositories.upload_repository import UploadRepository
from app.schemas.extraction import AuctionExtraction
from app.services.generator.excel_generator import ExcelGenerator
from app.services.generator.word_generator import WordGenerator
from app.services.llm.groq_service import GroqService
from app.services.llm.validator import ExtractionValidator
from app.services.ocr.text_extractor import TextExtractor
from app.services.preprocessing.image_enhancer import ImageEnhancer
from app.utils.regex import extract_regex_hints

logger = get_logger(__name__)


class AuctionProcessingPipeline:
    """Orchestrate OCR, LLM extraction, validation, persistence, and outputs."""

    def __init__(self, db: AsyncSession) -> None:
        self.upload_repo = UploadRepository(db)
        self.auction_repo = AuctionRepository(db)
        self.enhancer = ImageEnhancer()
        self.text_extractor = TextExtractor()
        self.groq = GroqService()
        self.validator = ExtractionValidator()
        self.word_generator = WordGenerator()
        self.excel_generator = ExcelGenerator()

    async def process_upload(self, upload_id: str) -> Auction:
        """Process an uploaded notice and return the final auction row."""
        upload = await self.upload_repo.get_by_id(upload_id)
        if upload is None:
            raise NotFoundError("Upload not found")

        existing = await self.auction_repo.get_by_upload_id(upload_id)
        if existing and upload.status == UploadStatus.COMPLETED.value:
            return existing

        try:
            await self.upload_repo.update_status(upload, UploadStatus.PROCESSING.value)
            input_path = Path(upload.file_path)

            processed_path = await self.enhancer.enhance(input_path)
            processed_path =input_path
            

            print("INPUT:", input_path)
            print("PROCESSED:", processed_path)
            upload.processed_file_path = str(processed_path)
            await self.upload_repo.save(upload)

            ocr_text = await self.text_extractor.extract(processed_path)
            

            print("=" * 100)
            print("OCR TEXT")
            print("=" * 100)
            print(ocr_text)
            print("=" * 100)


            if not ocr_text.strip():
                raise ProcessingError("OCR did not return readable text")

            regex_hints = extract_regex_hints(ocr_text)
            print("=" * 100)
            print("REGEX")
            print(regex_hints)
            
            llm_json = await self.groq.extract_auction_data(ocr_text, regex_hints)
            print("=" * 100)
            print("LLM OUTPUT")
            print(llm_json)
            print("=" * 100)
            
            extraction = self.validator.validate(llm_json, regex_hints, ocr_text)
            print("=" * 100)
            print("VALIDATED")
            print(extraction.model_dump())
            print("=" * 100)

            auction = existing or self._build_auction(upload.id, upload.listing_id)
            self._apply_extraction(auction, extraction, ocr_text, regex_hints.model_dump(), llm_json)
            auction = await self.auction_repo.create(auction) if existing is None else await self.auction_repo.save(auction)

            word_path = await self.word_generator.generate(auction)
            excel_path = await self.excel_generator.generate(auction)
            auction.word_path = str(word_path)
            auction.excel_path = str(excel_path)
            auction = await self.auction_repo.save(auction)
            await self.upload_repo.update_status(upload, UploadStatus.COMPLETED.value)
            return auction
        except Exception as exc:
            logger.exception("Failed to process upload %s", upload_id)
            await self.upload_repo.update_status(upload, UploadStatus.FAILED.value, str(exc))
            if isinstance(exc, ProcessingError):
                raise
            raise ProcessingError(str(exc)) from exc

    def _build_auction(self, upload_id: str, listing_id: str) -> Auction:
        return Auction(upload_id=upload_id, listing_id=listing_id)

    def _apply_extraction(
        self,
        auction: Auction,
        extraction: AuctionExtraction,
        ocr_text: str,
        regex_json: dict,
        llm_json: dict,
    ) -> None:
        data = extraction.model_dump()
        auction.bank_name = data["bank_name"]
        auction.borrower_name = data["borrower_name"]
        auction.loan_number = data["loan_number"]
        auction.auction_type = data["auction_type"]
        auction.property_type = data["property_type"]
        auction.property_category = data["property_category"]
        auction.asset_category = data["asset_category"]
        auction.movable_immovable = data["movable_immovable"]
        auction.possession_type = data["possession_type"]
        auction.reserve_price = data["reserve_price"]
        auction.emd = data["emd"]
        auction.demand_notice_date = data["demand_notice_date"]
        auction.symbolic_possession_date = data["symbolic_possession_date"]
        auction.auction_date = data["auction_date"]
        auction.property_address = data["property_address"]
        auction.district = data["district"]
        auction.state = data["state"]
        auction.beneficiary_bank = data["beneficiary_bank"]
        auction.ifsc = data["ifsc"]
        auction.contact_person = data["contact_person"]
        auction.contact_number = data["contact_number"]
        auction.website = data["website"]
        auction.description = data["description"]
        auction.summary = data["summary"]
        auction.who = data["who"]
        auction.whom = data["whom"]
        auction.where_location = data["where"]
        auction.when_details = data["when"]
        auction.confidence_score = data["confidence_score"]
        auction.raw_ocr_text = ocr_text
        auction.regex_json = regex_json
        auction.llm_json = llm_json

