"""
Auction AI Application.

FastAPI Entry Point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import text

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logger import get_logger
from app.database.base import Base
from app.database.connection import engine

from app.models.auction import Auction
from app.models.auction_processing_session import AuctionProcessingSession
from app.models.upload import Upload

settings = get_settings()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """

    logger.info("Starting Auction AI Application...")

    provider_name = "OpenAI" if (settings.llm_provider or "").lower() == "openai" else "Gemini"
    model_name = settings.openai_model if provider_name == "OpenAI" else settings.gemini_model
    logger.info("Selected LLM Provider: %s", provider_name)
    logger.info("Selected Model: %s", model_name)

    try:

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
            # Drop obsolete columns to prevent database default value errors on insert
            for col_name in ["bank_name", "branch_name", "dues_amount", "are_you_interested"]:
                try:
                    await conn.execute(text(f"ALTER TABLE auctions DROP COLUMN {col_name}"))
                    logger.info("Schema migration: Dropped obsolete column %s.", col_name)
                except Exception as e:
                    logger.debug("Obsolete column %s drop failed (might not exist): %s", col_name, e)

            # Alter/migrate table columns
            for col_sql, col_name, action_desc in [
                ("ALTER TABLE auctions ADD COLUMN possession_type VARCHAR(100) DEFAULT ''", "possession_type", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN asset_id VARCHAR(100) DEFAULT ''", "asset_id", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN notice_auction_id VARCHAR(100) DEFAULT ''", "notice_auction_id", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN payment_type VARCHAR(50) DEFAULT ''", "payment_type", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN remarks TEXT DEFAULT ''", "remarks", "Added column"),
                ("ALTER TABLE auctions MODIFY COLUMN borrower TEXT", "borrower", "Modified column type of")
            ]:
                try:
                    await conn.execute(text(col_sql))
                    logger.info("Schema migration: %s %s to/in auctions table.", action_desc, col_name)
                except Exception as e:
                    logger.debug("Query for %s might have already run, or SQLite fallback: %s", col_name, e)

        logger.info("Database initialized successfully.")

    except Exception as exc:

        logger.exception(
            "Database initialization failed.",
        )

        raise exc

    yield

    logger.info("Stopping Auction AI Application...")

app = FastAPI(

    title="Auction AI API",

    description="""
AI-powered auction newspaper extraction system.

Features:
- Image Upload
- Image Enhancement
- OCR
- Regex Extraction
- Gemini AI Extraction
- Field Validation
- Database Storage
- REST API
""",

    version="1.0.0",

    lifespan=lifespan,

    docs_url="/docs",

    redoc_url="/redoc",

    openapi_url="/openapi.json",

)

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

app.include_router(

    api_router,

    prefix="/api/v1",

)

@app.get(
    "/",
    tags=["Root"],
)
async def root():
    """
    Root dashboard UI endpoint.
    """
    import os
    from fastapi.responses import HTMLResponse

    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return HTMLResponse(
        content="<h1>Dashboard HTML template not found.</h1>",
        status_code=404
    )

@app.get(
    "/ping",
    tags=["Health"],
)
async def ping():
    """
    Ping endpoint.
    """

    return {

        "message": "pong",

    }

@app.exception_handler(Exception)
async def global_exception_handler(
    request,
    exc: Exception,
):
    """
    Handle unexpected exceptions.
    """

    logger.exception(
        str(exc),
    )

    return JSONResponse(

        status_code=500,

        content={

            "success": False,

            "message": "Internal Server Error",

            "detail": str(exc),

        },

    )

@app.get(
    "/info",
    tags=["Application"],
)
async def application_info():
    """
    Application information.
    """

    return {

        "application": "Auction AI",

        "version": "1.0.0",

        "environment": settings.environment,

        "debug": settings.debug,

    }

if __name__ == "__main__":

    uvicorn.run(

        "app.main:app",

        host=settings.host,

        port=settings.port,

        reload=settings.reload,

    )