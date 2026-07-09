"""Upload repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.upload import Upload


class UploadRepository:
    """Database operations for uploads."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, upload: Upload) -> Upload:
          self.db.add(upload)

          await self.db.flush()
          await self.db.commit()

          await self.db.refresh(upload)

          return upload

    

    async def get_by_id(self, upload_id: str) -> Upload | None:
        result = await self.db.execute(select(Upload).where(Upload.id == upload_id))
        return result.scalar_one_or_none()

    async def get_by_listing_id(self, listing_id: str) -> Upload | None:
        result = await self.db.execute(select(Upload).where(Upload.listing_id == listing_id))
        return result.scalar_one_or_none()

    async def update_status(self, upload: Upload, status: str, error_message: str | None = None) -> Upload:
        upload.status = status
        upload.error_message = error_message
        await self.db.commit()
        await self.db.refresh(upload)
        return upload

    async def save(self, upload: Upload) -> Upload:
        await self.db.commit()
        await self.db.refresh(upload)
        return upload

