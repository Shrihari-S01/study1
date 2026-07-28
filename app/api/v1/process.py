"""
Processing API.

Auction processing endpoints.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

from app.services.pipeline import AuctionPipeline

from app.schemas.response import APIResponse

router = APIRouter(
    prefix="/process",
    tags=["Processing"],
)

# ==========================================================
# Process Newspaper
# ==========================================================

@router.post(
    "/",
    response_model=APIResponse,
    summary="Process Newspaper",
)
async def process_newspaper(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and process newspaper.
    """

    try:

        pipeline = AuctionPipeline(db)

        result = await pipeline.run(
            file,
        )

        return APIResponse(

            success=True,

            message="Processing completed successfully.",

            data=result,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )
    
# ==========================================================
# Process Existing Image
# ==========================================================

@router.post(
    "/image",
    response_model=APIResponse,
    summary="Process Existing Image",
)
async def process_image(
    image_path: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Process an existing image file.
    """

    try:

        pipeline = AuctionPipeline(
            db,
        )

        result = await pipeline.process_image_path(
            image_path,
        )

        return APIResponse(

            success=True,

            message="Image processed successfully.",

            data=result,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )


# ==========================================================
# Batch Processing
# ==========================================================

@router.post(
    "/batch",
    response_model=APIResponse,
    summary="Batch Processing",
)
async def batch_process(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Process multiple newspaper images.
    """

    try:

        pipeline = AuctionPipeline(
            db,
        )

        result = await pipeline.run_batch(
            files,
        )

        return APIResponse(

            success=True,

            message="Batch processing completed.",

            data=result,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )