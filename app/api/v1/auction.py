"""
Auction API.

Auction record endpoints.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

from app.schemas.response import APIResponse

from app.services.storage.database_service import DatabaseService

router = APIRouter(
    tags=["Auction"],
)

# ==========================================================
# Get All Auctions
# ==========================================================

@router.get(
    "/",
    response_model=APIResponse,
    summary="Get All Auctions",
)
async def get_all_auctions(
    db: AsyncSession = Depends(get_db),
):
    """
    Return all auction records.
    """

    try:

        database = DatabaseService(
            db,
        )

        records = await database.get_all_auctions()

        return APIResponse(

            success=True,

            message="Auction records retrieved successfully.",

            data=records,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )
    
# ==========================================================
# Auction Statistics
# ==========================================================

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

        database = DatabaseService(
            db,
        )

        statistics = await database.statistics()

        return APIResponse(

            success=True,

            message="Auction statistics retrieved successfully.",

            data=statistics,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )


# ==========================================================
# Auction Count
# ==========================================================

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

        database = DatabaseService(
            db,
        )

        count = await database.count_auctions()

        return APIResponse(

            success=True,

            message="Auction count retrieved successfully.",

            data={

                "total_auctions": count,

            },

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )





# ==========================================================
# Get Auctions By Upload ID
# ==========================================================

@router.get(
    "/upload/{upload_id}",
    response_model=APIResponse,
    summary="Get Auctions By Upload",
)
async def get_auctions_by_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return all auction records
    belonging to one upload.
    """

    try:

        database = DatabaseService(
            db,
        )

        records = await database.get_auctions_by_upload(
            upload_id,
        )

        return APIResponse(

            success=True,

            message="Auction records retrieved successfully.",

            data=records,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )


# ==========================================================
# Search Auctions
# ==========================================================

@router.get(
    "/search/{keyword}",
    response_model=APIResponse,
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

        database = DatabaseService(
            db,
        )

        records = await database.search_auctions(
            keyword,
        )

        return APIResponse(

            success=True,

            message="Search completed successfully.",

            data=records,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )


# ==========================================================
# Get Auction By ID
# ==========================================================

@router.get(
    "/{auction_id}",
    response_model=APIResponse,
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

        database = DatabaseService(
            db,
        )

        record = await database.get_auction(
            auction_id,
        )

        return APIResponse(

            success=True,

            message="Auction record found.",

            data=record,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=404,

            detail=str(exc),

        )


# ==========================================================
# Delete Auction
# ==========================================================

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

        database = DatabaseService(
            db,
        )

        await database.delete_auction(
            auction_id,
        )

        return APIResponse(

            success=True,

            message="Auction deleted successfully.",

            data=None,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )