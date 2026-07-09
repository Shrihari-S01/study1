"""Processing endpoints."""

from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.auction import AuctionProcessResponse, AuctionRead
from app.schemas.response import ApiResponse
from app.services.pipeline import AuctionProcessingPipeline

router = APIRouter()


@router.post("/{upload_id}", response_model=ApiResponse[AuctionProcessResponse], status_code=status.HTTP_202_ACCEPTED)
async def process_upload(upload_id: str, db: DbSession) -> ApiResponse[AuctionProcessResponse]:
    """Process an uploaded notice synchronously and generate outputs."""
    auction = await AuctionProcessingPipeline(db).process_upload(upload_id)
    payload = AuctionProcessResponse(
        upload_id=upload_id,
        auction=AuctionRead.model_validate(auction),
        word_download_url=f"/api/v1/downloads/{auction.id}/word",
        excel_download_url=f"/api/v1/downloads/{auction.id}/excel",
    )
    return ApiResponse(message="Auction notice processed successfully", data=payload)


