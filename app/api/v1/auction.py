"""Auction query endpoints."""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.core.exceptions import NotFoundError
from app.repositories.auction_repository import AuctionRepository
from app.schemas.auction import AuctionRead
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[list[AuctionRead]])
async def list_auctions(
    db: DbSession,
    search: str | None = Query(default=None, description="Search listing, bank, borrower, district, or loan number"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[AuctionRead]]:
    """List processed auction records."""
    auctions = await AuctionRepository(db).list(search=search, limit=limit, offset=offset)
    return ApiResponse(data=[AuctionRead.model_validate(auction) for auction in auctions])


@router.get("/{auction_id}", response_model=ApiResponse[AuctionRead])
async def get_auction(auction_id: str, db: DbSession) -> ApiResponse[AuctionRead]:
    """Get one auction record."""
    auction = await AuctionRepository(db).get_by_id(auction_id)
    if auction is None:
        raise NotFoundError("Auction not found")
    return ApiResponse(data=AuctionRead.model_validate(auction))


@router.get("/{auction_id}/ocr", response_model=ApiResponse[dict[str, str]])
async def get_ocr_text(auction_id: str, db: DbSession) -> ApiResponse[dict[str, str]]:
    """Return raw OCR text for audit/debugging."""
    auction = await AuctionRepository(db).get_by_id(auction_id)
    if auction is None:
        raise NotFoundError("Auction not found")
    return ApiResponse(data={"listing_id": auction.listing_id, "ocr_text": auction.raw_ocr_text or ""})

