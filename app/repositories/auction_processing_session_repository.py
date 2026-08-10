"""
Auction Processing Session Repository.

Database access layer for storing, retrieving, and updating stateful auction extraction sessions.
Includes automatic table creation fallback to guarantee table existence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction_processing_session import AuctionProcessingSession
from app.database.base import Base
from app.core.logger import get_logger

logger = get_logger(__name__)

class AuctionProcessingSessionRepository:
    """
    Repository managing database interactions for AuctionProcessingSession.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
        self,
        processing_id: str,
        file_name: str,
        document_type: str,
        extracted_json: Any,
        canonical_json: Any = None,
        mapped_payload: Any = None,
        consistency_report: Any = None,
        status: str = "READY_FOR_REVIEW",
    ) -> AuctionProcessingSession:
        """
        Create and persist a new auction processing session in the database.
        Includes automatic table creation fallback if the table is missing.
        """
        session_obj = AuctionProcessingSession(
            processing_id=processing_id,
            file_name=file_name,
            document_type=document_type,
            status=status,
            extracted_json=extracted_json,
            canonical_json=canonical_json,
            mapped_payload=mapped_payload,
            consistency_report=consistency_report,
            completed=False,
        )

        try:
            self.db.add(session_obj)
            await self.db.commit()
            await self.db.refresh(session_obj)
        except Exception as err:
            err_str = str(err).lower()
            if "doesn't exist" in err_str or "no such table" in err_str:
                logger.warning("[%s] Table auction_processing_sessions missing. Executing auto-creation fallback...", processing_id)
                await self.db.rollback()
                async with self.db.bind.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                
                # Re-add session after table creation
                session_obj = AuctionProcessingSession(
                    processing_id=processing_id,
                    file_name=file_name,
                    document_type=document_type,
                    status=status,
                    extracted_json=extracted_json,
                    canonical_json=canonical_json,
                    mapped_payload=mapped_payload,
                    consistency_report=consistency_report,
                    completed=False,
                )
                self.db.add(session_obj)
                await self.db.commit()
                await self.db.refresh(session_obj)
            else:
                raise err

        logger.info(
            "[%s] DB SESSION CREATED SUCCESS - status='%s', file='%s', records=%d",
            processing_id,
            status,
            file_name,
            len(extracted_json) if isinstance(extracted_json, list) else 1,
        )
        return session_obj

    async def get_by_processing_id(self, processing_id: str) -> Optional[AuctionProcessingSession]:
        """
        Retrieve auction processing session from database by processing_id.
        """
        try:
            stmt = select(AuctionProcessingSession).where(AuctionProcessingSession.processing_id == processing_id)
            result = await self.db.execute(stmt)
            session_obj = result.scalars().first()

            if session_obj:
                logger.info(
                    "[%s] DB SESSION RETRIEVED - status='%s', completed=%s, file='%s'",
                    processing_id,
                    session_obj.status,
                    session_obj.completed,
                    session_obj.file_name,
                )
            else:
                logger.warning("[%s] DB SESSION NOT FOUND in database table auction_processing_sessions", processing_id)

            return session_obj
        except Exception as err:
            logger.warning("[%s] DB session query exception: %s", processing_id, err)
            return None

    async def update_status(
        self,
        processing_id: str,
        status: str,
        php_record_id: str = "",
        php_response_message: str = "",
        completed: bool = False,
        error_detail: str = "",
    ) -> Optional[AuctionProcessingSession]:
        """
        Update session status, PHP record ID, and completion state in database.
        """
        session_obj = await self.get_by_processing_id(processing_id)
        if not session_obj:
            logger.error("[%s] Cannot update DB session - session not found.", processing_id)
            return None

        session_obj.status = status
        if php_record_id:
            session_obj.php_record_id = php_record_id
        if php_response_message:
            session_obj.php_response_message = php_response_message
        if error_detail:
            session_obj.error_detail = error_detail

        session_obj.completed = completed
        await self.db.commit()
        await self.db.refresh(session_obj)

        logger.info("[%s] DB SESSION UPDATED - new_status='%s', completed=%s, record_id='%s'", processing_id, status, completed, php_record_id)
        return session_obj
