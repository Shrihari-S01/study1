"""
Main API Router.

Registers all API routes.
"""

from fastapi import APIRouter

from app.api.v1.upload import router as upload_router
from app.api.v1.auction import router as auction_router
from app.api.v1.process import router as process_router
from app.api.v1.health import router as health_router

api_router = APIRouter()



api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)



api_router.include_router(
    upload_router,
    prefix="/upload",
    tags=["Upload"],
)



api_router.include_router(
    process_router,
    prefix="/process",
    tags=["Process"],
)

api_router.include_router(
    auction_router,
    prefix="/auction",
    tags=["Auction"],
)