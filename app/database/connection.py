"""
Database connection.

Creates SQLAlchemy Async Engine and Session.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Optional:
# from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.logger import get_logger


# ==========================================================
# Configuration
# ==========================================================

settings = get_settings()

logger = get_logger(__name__)


# ==========================================================
# Async Engine & Session Initialization
# ==========================================================

def init_database() -> tuple[AsyncEngine, async_sessionmaker]:
    url = settings.database_url
    dialect = "mysql"

    # Synchronous socket ping to check port 3306 on localhost/127.0.0.1
    if "localhost" in url or "127.0.0.1" in url:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", 3306))
            s.close()
        except Exception:
            logger.warning(
                "MySQL port 3306 on localhost is refused. Falling back to local SQLite database."
            )
            url = "sqlite+aiosqlite:///./auction_ai.db"
            dialect = "sqlite"

    if dialect == "sqlite":
        # SQLite does not support pool_size and max_overflow parameters
        eng = create_async_engine(
            url,
            echo=settings.database_echo,
            future=True,
            pool_pre_ping=True,
        )
    else:
        eng = create_async_engine(
            url,
            echo=settings.database_echo,
            future=True,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
        )

    logger.info("=" * 80)
    logger.info("Database Engine Initialized")
    logger.info("Database URL      : %s", url)
    logger.info("Database Dialect  : %s", dialect)
    logger.info("=" * 80)

    session_factory = async_sessionmaker(
        bind=eng,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    return eng, session_factory

engine, AsyncSessionLocal = init_database()


# ==========================================================
# Database Dependency
# ==========================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI database dependency.
    """

    async with AsyncSessionLocal() as session:

        try:

            yield session

        except Exception:

            await session.rollback()
            raise

        finally:

            await session.close()


# ==========================================================
# Database Connection Test
# ==========================================================

async def check_database_connection() -> bool:
    """
    Check whether database connection is working.
    """

    try:

        async with engine.connect() as connection:

            await connection.execute(
                text("SELECT 1")
            )

        logger.info(
            "Database connection successful."
        )

        return True

    except SQLAlchemyError:

        logger.exception(
            "Database connection failed."
        )

        return False

    except Exception:

        logger.exception(
            "Unexpected database error."
        )

        return False


# ==========================================================
# Shutdown
# ==========================================================

async def close_database() -> None:
    """
    Dispose database engine.
    """

    logger.info(
        "Closing database engine..."
    )

    await engine.dispose()

    logger.info(
        "Database engine closed."
    )