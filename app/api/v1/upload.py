"""
Upload API.

Handles auction newspaper uploads.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.services.pipeline import AuctionPipeline

router = APIRouter(
    tags=["Upload"],
)

@router.post(
    "/",
    response_model=APIResponse,
    summary="Upload Newspaper",
)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload newspaper image and
    process auction notices.
    """

    if file.filename is None:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Filename is missing.",

        )

    allowed_extensions = {

        ".jpg",

        ".jpeg",

        ".png",

        ".bmp",

        ".tif",

        ".tiff",

        ".webp",
    }

    extension = Path(
        file.filename,
    ).suffix.lower()

    if extension not in allowed_extensions:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail=f"Unsupported file format: {extension}",

        )

    try:

        pipeline = AuctionPipeline(
            db,
        )

        result = await pipeline.run(
            file,
        )

        return APIResponse(

            success=True,

            message="Auction newspaper processed successfully.",

            data=result,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=str(exc),

        )

@router.post(
    "/document/",
    response_model=APIResponse,
    summary="Upload PDF Document",
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload multi-page PDF document and
    process auction notices.
    """

    if file.filename is None:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Filename is missing.",

        )

    allowed_extensions = {".pdf"}

    extension = Path(
        file.filename,
    ).suffix.lower()

    if extension not in allowed_extensions:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail=f"Unsupported file format: {extension}. Only PDF is allowed.",

        )

    try:
        from app.services.document_pipeline import DocumentPipeline

        pipeline = DocumentPipeline(
            db,
        )

        result = await pipeline.run(
            file,
        )

        return APIResponse(

            success=True,

            message="Auction document processed successfully.",

            data=result,

        )

    except Exception as exc:

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=str(exc),

        )

