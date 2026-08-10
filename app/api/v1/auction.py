"""
Auction API.

Auction record endpoints for querying and managing database records.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.auction import AuctionResponse
from app.services.storage.database_service import DatabaseService
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    tags=["Auction"],
)

@router.get(
    "/",
    response_model=APIResponse[List[AuctionResponse]],
    summary="Get All Auctions",
)
async def get_all_auctions(
    db: AsyncSession = Depends(get_db),
):
    """
    Return all auction records.
    """
    try:
        database = DatabaseService(db)
        records = await database.get_all_auctions()
        data = [AuctionResponse.model_validate(rec) for rec in records]

        return APIResponse(
            success=True,
            message="Auction records retrieved successfully.",
            data=data,
        )
    except Exception as exc:
        logger.exception("Failed to retrieve all auctions: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get(
    "/statistics",
    response_model=APIResponse,
    summary="Auction Statistics",
)
async def auction_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Return auction statistics.
    """
    try:
        database = DatabaseService(db)
        statistics = await database.statistics()

        return APIResponse(
            success=True,
            message="Auction statistics retrieved successfully.",
            data=statistics,
        )
    except Exception as exc:
        logger.exception("Failed to retrieve auction statistics: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get(
    "/count",
    response_model=APIResponse,
    summary="Auction Count",
)
async def auction_count(
    db: AsyncSession = Depends(get_db),
):
    """
    Return total auction count.
    """
    try:
        database = DatabaseService(db)
        count = await database.count_auctions()

        return APIResponse(
            success=True,
            message="Auction count retrieved successfully.",
            data={
                "total_auctions": count,
            },
        )
    except Exception as exc:
        logger.exception("Failed to retrieve auction count: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get(
    "/upload/{upload_id}",
    response_model=APIResponse[List[AuctionResponse]],
    summary="Get Auctions By Upload",
)
async def get_auctions_by_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return all auction records belonging to one upload.
    """
    try:
        database = DatabaseService(db)
        records = await database.get_auctions_by_upload(upload_id)
        data = [AuctionResponse.model_validate(rec) for rec in records]

        return APIResponse(
            success=True,
            message="Auction records retrieved successfully.",
            data=data,
        )
    except Exception as exc:
        logger.exception("Failed to retrieve auctions for upload %s: %s", upload_id, exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get(
    "/search/{keyword}",
    response_model=APIResponse[List[AuctionResponse]],
    summary="Search Auctions",
)
async def search_auctions(
    keyword: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Search auction records.
    """
    try:
        database = DatabaseService(db)
        records = await database.search_auctions(keyword)
        data = [AuctionResponse.model_validate(rec) for rec in records]

        return APIResponse(
            success=True,
            message="Search completed successfully.",
            data=data,
        )
    except Exception as exc:
        logger.exception("Failed to search auctions for keyword '%s': %s", keyword, exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get(
    "/{auction_id}",
    response_model=APIResponse[Optional[AuctionResponse]],
    summary="Get Auction By ID",
)
async def get_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return a single auction record.
    """
    try:
        database = DatabaseService(db)
        record = await database.get_auction(auction_id)
        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Auction record with ID '{auction_id}' not found.",
            )

        data = AuctionResponse.model_validate(record)

        return APIResponse(
            success=True,
            message="Auction record found.",
            data=data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve auction %s: %s", auction_id, exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.delete(
    "/{auction_id}",
    response_model=APIResponse,
    summary="Delete Auction",
)
async def delete_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete auction record.
    """
    try:
        database = DatabaseService(db)
        await database.delete_auction(auction_id)

        return APIResponse(
            success=True,
            message="Auction deleted successfully.",
            data=None,
        )
    except Exception as exc:
        logger.exception("Failed to delete auction %s: %s", auction_id, exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )