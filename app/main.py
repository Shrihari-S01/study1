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

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logger import get_logger
from app.database.base import Base
from app.database.connection import engine

logger = get_logger(__name__)

settings = get_settings()


# ==========================================================
# Application Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """

    logger.info("Starting Auction AI Application...")

    try:

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
            # Alter/migrate table columns
            from sqlalchemy import text
            for col_sql, col_name, action_desc in [
                ("ALTER TABLE auctions ADD COLUMN bank_name VARCHAR(255) DEFAULT ''", "bank_name", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN branch_name VARCHAR(255) DEFAULT ''", "branch_name", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN possession_type VARCHAR(100) DEFAULT ''", "possession_type", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN dues_amount DECIMAL(15, 2) DEFAULT 0.00", "dues_amount", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN asset_id VARCHAR(100) DEFAULT ''", "asset_id", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN notice_auction_id VARCHAR(100) DEFAULT ''", "notice_auction_id", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN payment_type VARCHAR(50) DEFAULT ''", "payment_type", "Added column"),
                ("ALTER TABLE auctions ADD COLUMN are_you_interested VARCHAR(10) DEFAULT ''", "are_you_interested", "Added column"),
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


# ==========================================================
# FastAPI Application
# ==========================================================

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


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)


# ==========================================================
# Include API Routes
# ==========================================================

app.include_router(

    api_router,

    prefix="/api/v1",

)


# ==========================================================
# Root Endpoint
# ==========================================================

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


# ==========================================================
# Ping Endpoint
# ==========================================================

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


# ==========================================================
# Global Exception Handler
# ==========================================================

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


# ==========================================================
# Startup Information
# ==========================================================

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


# ==========================================================
# Run Application
# ==========================================================

if __name__ == "__main__":

    uvicorn.run(

        "app.main:app",

        host=settings.host,

        port=settings.port,

        reload=settings.reload,

    )