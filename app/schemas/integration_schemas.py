"""
Integration API Schemas.

Dedicated Pydantic models for Angular frontend integration:
- DocumentProcessingResponse: Phase 1 pure AI document extraction output (Zero PHP fields).
- AuctionSubmissionRequest: Phase 2 user submission input (processing_id or extracted_auction + Angular master selections).
- AuctionSubmissionResponse: Phase 2 PHP API insertion result.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DocumentProcessingResponse(BaseModel):
    """
    Response model for Phase 1 POST /integration/process-document.
    Contains strictly document processing and AI extraction details.
    """
    success: bool = Field(..., description="Overall document processing & extraction success")
    stage: str = Field(default="DOCUMENT_PROCESSED", description="Current workflow stage")
    processing_id: str = Field(..., description="Unique UUID for auditability")
    file_name: str = Field(..., description="Uploaded document file name")
    document_type: str = Field(..., description="Detected document type (IMAGE or PDF)")
    processing_time_seconds: float = Field(..., description="Total execution time in seconds")
    summary: Dict[str, int] = Field(
        ...,
        description="Counts: total_records, extracted_records, validation_failed",
    )
    records: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted auction record dictionaries ready for UI review",
    )
    message: str = Field(..., description="Human-readable status summary message")

class AuctionSubmissionRequest(BaseModel):
    """
    Phase 2 Submission Request DTO sent by Angular frontend after user review.
    Supports processing_id lookup OR direct extracted_auction JSON payload + Angular master selections.
    """
    processing_id: Optional[str] = Field(default="", description="Optional processing session ID from Phase 1")
    
    # Mandatory Master Selections
    vendor_id: str = Field(..., description="Selected Master Vendor ID (Mandatory)")
    section_id: str = Field(..., description="Selected Master Section ID (Mandatory)")
    part_id: str = Field(..., description="Selected Master Part ID (Mandatory)")
    auction_type: str = Field(..., description="Selected Auction Type (Mandatory)")
    payment_type: str = Field(..., description="Selected Payment Type (Mandatory)")

    # Optional PHP Contract Business/Master Fields (Defaults to empty strings if omitted)
    category_id: Optional[str] = Field(default="", description="Optional Category ID")
    item_id: Optional[str] = Field(default="", description="Optional Item ID")
    demo_auction: Optional[str] = Field(default="0", description="Optional Demo Auction Flag")
    borrower_required: Optional[str] = Field(default="0", description="Optional Borrower Required Flag")
    auction_interested: Optional[str] = Field(default="0", description="Optional Auction Interested Flag")
    auction_image_url: Optional[str] = Field(default="", description="Optional Override Image URL")
    auction_supporting_docs_1: Optional[str] = Field(default="", description="Optional Override Supporting Doc 1 URL")
    auction_supporting_docs_2: Optional[str] = Field(default="", description="Optional Override Supporting Doc 2 URL")

    # Extracted Auction Payload (Optional if processing_id provided)
    extracted_auction: Optional[Dict[str, Any]] = Field(default=None, description="Extracted auction JSON dictionary from Phase 1")
    extracted_auctions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Extracted auction JSON dictionaries array from Phase 1")

class AuctionSubmissionResult(BaseModel):
    """
    Per-record status result for batch PHP insertion.
    """
    record_no: int = Field(..., description="1-based record index in batch")
    auction_number: str = Field(default="", description="Extracted auction number or lot ID")
    status: str = Field(..., description="SUCCESS or FAILED")
    needs_manual_review: bool = Field(default=False, description="Flag indicating if record needs manual review due to missing optional fields like product_location")
    php_record_id: Optional[str] = Field(default="", description="Returned PHP record ID if inserted")
    error: Optional[str] = Field(default="", description="Error description if record failed")

class AuctionSubmissionResponse(BaseModel):
    """
    Response model for Phase 2 POST /integration/submit-auction.
    Contains PHP Master Software insertion results and record IDs for single/multi-record batches.
    """
    success: bool = Field(..., description="PHP insertion success status")
    stage: str = Field(default="AUCTION_SUBMITTED", description="Current workflow stage")
    processing_id: str = Field(..., description="Unique processing UUID")
    php_insert_success: bool = Field(..., description="Whether PHP API insert succeeded")
    total_records: int = Field(default=0, description="Total extracted records in batch")
    inserted: int = Field(default=0, description="Count of successfully inserted records")
    failed: int = Field(default=0, description="Count of failed record insertions")
    processing_time: float = Field(default=0.0, description="Total batch submission processing time in seconds")
    results: List[AuctionSubmissionResult] = Field(default_factory=list, description="Per-record insertion results")
    php_record_id: Optional[str] = Field(default="", description="Returned PHP record ID(s)")
    php_response_message: Optional[str] = Field(default="", description="Message returned by PHP API")
    php_response_raw: Optional[Dict[str, Any]] = Field(default=None, description="Raw response payload from PHP")
    error_detail: Optional[str] = Field(default=None, description="Error detail if insertion failed")
    message: str = Field(..., description="Human-readable status message")

# Backward Compatibility Schemas
class IntegrationMasterData(BaseModel):
    vendor_id: str = Field(default="", description="Vendor ID")
    section_id: str = Field(default="", description="Section ID")
    part_id: str = Field(default="", description="Part ID")
    auction_type: str = Field(default="", description="Auction Type")
    payment_type: str = Field(default="", description="Payment Type")
    category_id: Optional[str] = Field(default="", description="Category ID")
    item_id: Optional[str] = Field(default="", description="Item ID")
    demo_auction: Optional[str] = Field(default="0", description="Demo Auction Flag")
    borrower_required: Optional[str] = Field(default="0", description="Borrower Required Flag")
    auction_interested: Optional[str] = Field(default="0", description="Auction Interested Flag")
    auction_image_url: Optional[str] = Field(default="", description="Override Image URL")
    auction_supporting_docs_1: Optional[str] = Field(default="", description="Override Doc 1 URL")
    auction_supporting_docs_2: Optional[str] = Field(default="", description="Override Doc 2 URL")

class RecordProcessingStatus(BaseModel):
    lot_index: int = Field(..., description="1-based index of lot in document")
    auction_number: str = Field(default="", description="Extracted Auction Number")
    validation_success: bool = Field(..., description="Whether record passed validation")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors if failed")
    consistency_report: Optional[Dict[str, Any]] = Field(default=None, description="Machine-readable consistency audit report")
    php_insert_success: bool = Field(default=False, description="Whether PHP API insert succeeded")
    php_record_id: Optional[str] = Field(default="", description="Returned PHP record ID")
    php_response_message: Optional[str] = Field(default="", description="Message returned by PHP API")
    php_response_raw: Optional[Dict[str, Any]] = Field(default=None, description="Raw response payload from PHP")
    error_detail: Optional[str] = Field(default=None, description="Error detail if insertion or validation failed")

class IntegrationResponse(BaseModel):
    success: bool = Field(..., description="Overall request success status")
    stage: str = Field(default="DOCUMENT_PROCESSED", description="Current workflow stage")
    next_action: str = Field(default="USER_REVIEW_REQUIRED", description="Next required action")
    php_skipped: bool = Field(default=False, description="Whether PHP insert was intentionally skipped")
    processing_id: str = Field(..., description="Unique UUID for end-to-end auditability")
    file_name: str = Field(..., description="Uploaded file name")
    document_type: str = Field(..., description="Detected document type (IMAGE or PDF)")
    processing_time_seconds: float = Field(..., description="Total elapsed execution time")
    summary: Dict[str, Any] = Field(..., description="Summary counts including total_lots, inserted, failed, failed_lots")
    processing_summary: Dict[str, int] = Field(default_factory=dict, description="Detailed summary")
    records: List[RecordProcessingStatus] = Field(default_factory=list, description="Individual record statuses")
    message: str = Field(..., description="Human-readable summary message")
