"""Health check endpoints."""

from fastapi import APIRouter

from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    """Return API health status."""
    return ApiResponse(data={"status": "healthy"})

