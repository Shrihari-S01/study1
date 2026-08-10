"""
Integration API Router.

Production-grade endpoints connecting Angular frontend with Python AI Orchestrator and PHP Master Software.
Strictly separates Phase 1 AI Document Extraction (File -> Extracted JSON) from Phase 2 Final Submission (Angular Master Values + Extracted JSON -> PHP API).
"""

from __future__ import annotations

from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.integration_schemas import (
    AuctionSubmissionRequest,
    AuctionSubmissionResponse,
    DocumentProcessingResponse,
    IntegrationMasterData,
    IntegrationResponse,
)
from app.services.integration.request_validation_service import RequestValidationService
from app.services.integration.upload_orchestration_service import UploadOrchestrationService
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/integration",
    tags=["Angular & PHP Integration"],
)

@router.post(
    "/process-document",
    response_model=DocumentProcessingResponse,
    summary="Phase 1: Pure AI Document Extraction (File Upload Only)",
    description="""
Phase 1 Endpoint: Receives document upload ONLY (Image or PDF) and executes OCR, Gemini Vision extraction,
field mapping, normalization, business defaults, and semantic consistency validation.

Swagger/OpenAPI parameters: Accept ONLY 'file'.
Returns extracted auction JSON dictionary ready for Angular UI review.
Does NOT generate PHP payload, does NOT call PHP insert API, and returns ZERO PHP fields.
""",
)
async def process_document(
    file: UploadFile = File(..., description="Uploaded Image or PDF auction document"),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute Phase 1 Pure AI Document Processing.
    Accepts ONLY file. Zero master inputs exposed or required.
    """
    try:
        content_bytes = await file.read()
        await file.seek(0)

        # File Upload Validation ONLY
        is_file_valid, file_val_msg = RequestValidationService.validate_file_upload(file, content_bytes)
        if not is_file_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "stage": "ERROR",
                    "processing_id": "",
                    "file_name": file.filename or "unknown",
                    "document_type": "UNKNOWN",
                    "processing_time_seconds": 0.0,
                    "summary": {"total_records": 0, "extracted_records": 0, "validation_failed": 1},
                    "records": [],
                    "message": file_val_msg,
                },
            )

        orchestrator = UploadOrchestrationService(db)
        result = await orchestrator.process_document(file)
        return result

    except Exception as exc:
        logger.exception("Fatal exception in /integration/process-document: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"AI Document Processing Error: {str(exc)}",
        )

@router.post(
    "/submit-auction",
    response_model=AuctionSubmissionResponse,
    summary="Phase 2: Final Submission & PHP Insertion",
    description="""
Phase 2 Endpoint: Accepts user-selected Angular master values (vendor_id, section_id, part_id, auction_type, payment_type)
and extracted_auction JSON dictionary.

Merges extracted auction data with user master values, formats PHP payload, and inserts directly into PHP Master Software.
""",
)
async def submit_auction(
    submission: AuctionSubmissionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute Phase 2 Final Submission & PHP Insertion.
    """
    try:
        # Validate Angular Master Selections
        master_data = IntegrationMasterData(
            vendor_id=submission.vendor_id,
            section_id=submission.section_id,
            part_id=submission.part_id,
            auction_type=submission.auction_type,
            payment_type=submission.payment_type,
        )

        is_master_valid, missing_fields, val_msg = RequestValidationService.validate_master_selections(master_data)
        if not is_master_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "stage": "ERROR",
                    "processing_id": "",
                    "php_insert_success": False,
                    "php_record_id": "",
                    "php_response_message": val_msg,
                    "php_response_raw": None,
                    "error_detail": val_msg,
                    "message": val_msg,
                },
            )

        orchestrator = UploadOrchestrationService(db)
        result = await orchestrator.submit_auction(submission)

        if not result.success and "No extracted auction data found" in (result.message or ""):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=result.model_dump(),
            )

        return result

    except Exception as exc:
        logger.exception("Fatal exception in /integration/submit-auction: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Auction Submission Error: {str(exc)}",
        )
