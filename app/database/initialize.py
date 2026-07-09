"""Database initialization helpers."""

from app.core.config import get_settings
from app.core.logger import get_logger


from app.models.auction import Auction
from app.models.upload import Upload

from app.database.base import Base
from app.database.connection import engine


logger = get_logger(__name__)


async def init_db() -> None:
    """Create tables and required directories."""
    settings = get_settings()
    for directory in (
        settings.upload_dir,
        settings.processed_dir,
        settings.word_output_dir,
        settings.excel_output_dir,
        settings.template_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

