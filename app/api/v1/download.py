"""Download endpoints."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.api.deps import DbSession
from app.core.constants import SUPPORTED_DOWNLOAD_TYPES
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.auction_repository import AuctionRepository

router = APIRouter()


@router.get("/{auction_id}/{file_type}")
async def download_generated_file(auction_id: str, file_type: str, db: DbSession) -> FileResponse:
    """Download generated Word or Excel output."""
    if file_type not in SUPPORTED_DOWNLOAD_TYPES:
        raise ValidationError("file_type must be 'word' or 'excel'")

    auction = await AuctionRepository(db).get_by_id(auction_id)
    if auction is None:
        raise NotFoundError("Auction not found")

    file_path = auction.word_path if file_type == "word" else auction.excel_path
    if not file_path:
        raise NotFoundError(f"{file_type.title()} output is not available")

    path = Path(file_path)
    if not path.exists():
        raise NotFoundError(f"{file_type.title()} output is not available")

    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if file_type == "word"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return FileResponse(path, media_type=media_type, filename=path.name)
