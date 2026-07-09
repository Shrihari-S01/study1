"""Upload schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadRead(BaseModel):
    """Upload metadata returned by API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str
    original_filename: str
    stored_filename: str
    content_type: str | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadCreateResponse(BaseModel):
    """Upload response with next processing route."""

    upload: UploadRead
    process_url: str

