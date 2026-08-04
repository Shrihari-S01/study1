"""
Health API.

Application health monitoring endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.pipeline import AuctionPipeline
from app.services.storage.database_service import DatabaseService

router = APIRouter()


# ==========================================================
# Application Health
# ==========================================================

@router.get(
    "/",
    summary="Application Health",
)
async def application_health(
    db: AsyncSession = Depends(get_db),
):
    """
    Application health status.
    """

    pipeline = AuctionPipeline(db)

    database = DatabaseService(db)

    return {

        "status": "Healthy",

        "application": "Auction AI",

        "version": "1.0.0",

        "pipeline": await pipeline.health_check(),

        "database": await database.health_check(),

    }


# ==========================================================
# Service Information
# ==========================================================

@router.get(
    "/info",
    summary="Application Information",
)
async def information(
    db: AsyncSession = Depends(get_db),
):
    """
    Application information.
    """

    pipeline = AuctionPipeline(db)

    return {

        "application": "Auction AI",

        "version": "1.0.0",

        "framework": "FastAPI",

        "pipeline": pipeline.info(),

    }


