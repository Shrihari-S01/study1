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
# Pipeline Health
# ==========================================================

@router.get(
    "/pipeline",
    summary="Pipeline Health",
)
async def pipeline_health(
    db: AsyncSession = Depends(get_db),
):
    """
    Pipeline health.
    """

    pipeline = AuctionPipeline(db)

    return await pipeline.health_check()


# ==========================================================
# Database Health
# ==========================================================

@router.get(
    "/database",
    summary="Database Health",
)
async def database_health(
    db: AsyncSession = Depends(get_db),
):
    database = DatabaseService(db)

    return await database.health_check()
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


# ==========================================================
# Statistics
# ==========================================================

@router.get(
    "/statistics",
    summary="Application Statistics",
)
async def statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Application statistics.
    """

    pipeline = AuctionPipeline(db)

    database = DatabaseService(db)

    return {

        "pipeline": await pipeline.statistics(),

        "database": await database.statistics(),

    }


# ==========================================================
# Readiness Check
# ==========================================================

@router.get(
    "/ready",
    summary="Readiness Check",
)
async def readiness(
    db: AsyncSession = Depends(get_db),
):
    """
    Readiness status.
    """

    pipeline = AuctionPipeline(db)

    database = DatabaseService(db)

    pipeline_ready = await pipeline.is_ready()

    database_ready = await database.is_ready()

    ready = pipeline_ready and database_ready

    return {

        "ready": ready,

        "status": "Ready" if ready else "Not Ready",

    }


# ==========================================================
# Liveness Check
# ==========================================================

@router.get(
    "/live",
    summary="Liveness Check",
)
async def liveness():
    """
    Liveness endpoint.
    """

    return {

        "alive": True,

        "status": "Running",

    }


