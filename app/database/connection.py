"""
Database connection.

Creates SQLAlchemy Async Engine and Session.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
# pyrefly: ignore [missing-import]
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

settings = get_settings()

logger = get_logger(__name__)

def _test_mysql_sync(host: str, port: int, user: str, password: str, database: str) -> bool:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((host, port))
        s.close()
    except Exception:
        logger.warning("MySQL port %s:%s not reachable. Falling back to SQLite.", host, port)
        return False
    try:
        import pymysql
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password,
            database=database, connect_timeout=3,
        )
        conn.close()
        return True
    except Exception as exc:
        logger.warning("MySQL connection test failed (%s). Falling back to SQLite.", exc)
        return False


def init_database() -> tuple[AsyncEngine, async_sessionmaker]:
    url = settings.database_url
    dialect = "mysql"

    mysql_ok = _test_mysql_sync(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
    )

    if not mysql_ok:
        url = "sqlite+aiosqlite:///./auction_ai.db"
        dialect = "sqlite"

    if dialect == "sqlite":
        eng = create_async_engine(url, echo=settings.database_echo, future=True)
    else:
        eng = create_async_engine(
            url, echo=settings.database_echo, future=True,
            pool_recycle=3600, pool_size=10, max_overflow=20,
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