"""
Database initialization.

Creates application directories and database tables.
"""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.logger import get_logger

from app.database.base import Base
from app.database.connection import (
    engine,
    check_database_connection,
)

# ==========================================================
# Import Models
# ==========================================================

# IMPORTANT:
# Import every model here so SQLAlchemy
# registers them before create_all().

from app.models.upload import Upload
from app.models.auction import Auction


logger = get_logger(__name__)

settings = get_settings()


# ==========================================================
# Create Directories
# ==========================================================

def create_directories() -> None:
    """
    Create required application directories.
    """

    directories = [

        settings.upload_dir,

        settings.original_dir,

        settings.processed_dir,

        settings.split_dir,

        settings.log_dir,

    ]

    for directory in directories:

        directory.mkdir(

            parents=True,

            exist_ok=True,

        )

        logger.info(

            "Directory Ready : %s",

            directory,

        )


# ==========================================================
# Create Database Tables
# ==========================================================

async def create_tables() -> None:
    """
    Create database tables.
    """

    try:

        async with engine.begin() as connection:

            await connection.run_sync(

                Base.metadata.create_all,

            )

        logger.info(

            "Database tables created successfully."

        )

    except SQLAlchemyError:

        logger.exception(

            "Failed to create database tables."

        )

        raise


# ==========================================================
# Initialize Application
# ==========================================================

async def initialize_database() -> None:
    """
    Initialize application.

    - Create folders
    - Check DB connection
    - Create tables
    """

    logger.info("=" * 80)

    logger.info(
        "Initializing Auction Intelligence API"
    )

    logger.info("=" * 80)

    # ------------------------------------------------------

    create_directories()

    # ------------------------------------------------------

    connected = await check_database_connection()

    if not connected:

        raise RuntimeError(

            "Unable to connect to MySQL."

        )

    # ------------------------------------------------------

    await create_tables()

    # ------------------------------------------------------

    logger.info("=" * 80)

    logger.info(
        "Application initialization completed successfully."
    )

    logger.info("=" * 80)