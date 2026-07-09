"""API router registration."""

from fastapi import APIRouter

from app.api.v1 import auction, download, health, process, upload

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(upload.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(process.router, prefix="/process", tags=["process"])
api_router.include_router(auction.router, prefix="/auctions", tags=["auctions"])
api_router.include_router(download.router, prefix="/downloads", tags=["downloads"])

