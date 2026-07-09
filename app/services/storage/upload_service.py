"""Upload service."""

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.upload import Upload
from app.repositories.upload_repository import UploadRepository
from app.services.storage.file_manager import FileManager
from app.utils.helper import generate_listing_id


class UploadService:
    """Handle upload persistence and upload metadata records."""

    def __init__(self, db: AsyncSession) -> None:
        self.repository = UploadRepository(db)
        self.file_manager = FileManager()

    # async def create_upload(self, file: UploadFile) -> Upload:
    #     """Store file and create an upload row."""
    #     listing_id = generate_listing_id()
    #     stored_path = await self.file_manager.save_upload(file, listing_id)
    #     upload = Upload(
    #         listing_id=listing_id,
    #         original_filename=file.filename or stored_path.name,
    #         stored_filename=stored_path.name,
    #         file_path=str(stored_path),
    #         content_type=file.content_type,
    #     )
    #     return await self.repository.create(upload)


    async def create_upload(self, file: UploadFile) -> Upload:
     print("Service Started")

     listing_id = generate_listing_id()
     print("Listing ID:", listing_id)

     stored_path = await self.file_manager.save_upload(file, listing_id)
     print("Saved File:", stored_path)

     upload = Upload(
        listing_id=listing_id,
        original_filename=file.filename or stored_path.name,
        stored_filename=stored_path.name,
        file_path=str(stored_path),
        content_type=file.content_type,
    )

     print("Upload Model Created")

     result = await self.repository.create(upload)

     print("Repository Returned")

     return result
