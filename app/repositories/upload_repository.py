"""
Upload Repository.

Handles all database operations related to uploads.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models.upload import Upload

logger = get_logger(__name__)

class UploadRepository:
    """
    Repository for Upload table.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:

        self.db = db

    async def create(
        self,
        upload: Upload,
    ) -> Upload:
        """
        Create a new upload.
        """

        self.db.add(upload)

        await self.db.commit()

        await self.db.refresh(upload)

        logger.info(
            "Upload created: %s",
            upload.upload_number,
        )

        return upload

    async def get_by_id(
        self,
        upload_id: str,
    ) -> Upload | None:
        """
        Get upload by primary key.
        """

        result = await self.db.execute(

            select(Upload).where(
                Upload.id == upload_id,
            )

        )

        return result.scalar_one_or_none()

    async def get_by_upload_number(
        self,
        upload_number: str,
    ) -> Upload | None:
        """
        Get upload using upload number.
        """

        result = await self.db.execute(

            select(Upload).where(
                Upload.upload_number == upload_number,
            )

        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
    ) -> list[Upload]:
        """
        Return all uploads.
        """

        result = await self.db.execute(

            select(Upload)

            .order_by(
                Upload.created_at.desc(),
            )

            .limit(limit)

        )

        return list(result.scalars().all())

    async def update(
        self,
        upload: Upload,
    ) -> Upload:
        """
        Save upload changes.
        """

        await self.db.commit()

        await self.db.refresh(upload)

        logger.info(
            "Upload updated: %s",
            upload.upload_number,
        )

        return upload

    async def update_status(
        self,
        upload: Upload,
        status: str,
        error_message: str = "",
    ) -> Upload:
        """
        Update upload status.
        """

        upload.status = status

        upload.error_message = error_message

        await self.db.commit()

        await self.db.refresh(upload)

        logger.info(
            "Upload status updated: %s -> %s",
            upload.upload_number,
            status,
        )

        return upload

    async def update_statistics(
        self,
        upload: Upload,
        total_notices: int,
        successful_notices: int,
        failed_notices: int,
        processing_time: float,
        confidence_score: float,
    ) -> Upload:
        """
        Update processing statistics.
        """

        upload.total_notices = total_notices

        upload.successful_notices = successful_notices

        upload.failed_notices = failed_notices

        upload.processing_time = processing_time

        upload.confidence_score = confidence_score

        await self.db.commit()

        await self.db.refresh(upload)

        logger.info(
            "Statistics updated for %s",
            upload.upload_number,
        )

        return upload

    async def delete(
        self,
        upload: Upload,
    ) -> None:
        """
        Delete upload.
        """

        await self.db.delete(upload)

        await self.db.commit()

        logger.info(
            "Upload deleted: %s",
            upload.upload_number,
        )

    async def exists(
        self,
        upload_id: str,
    ) -> bool:
        """
        Check upload existence.
        """

        upload = await self.get_by_id(
            upload_id,
        )

        return upload is not None

    async def count(
        self,
    ) -> int:
        """
        Return total uploads count.
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(Upload.id))
        )

        return result.scalar_one() or 0