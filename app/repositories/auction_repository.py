"""
Auction Repository.

Handles all database operations for auction records.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models.auction import Auction

logger = get_logger(__name__)


class AuctionRepository:
    """
    Repository for Auction table.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:

        self.db = db

    # ==========================================================
    # Create Auction
    # ==========================================================

    async def create(
        self,
        auction: Auction,
    ) -> Auction:
        """
        Create a single auction.
        """

        self.db.add(auction)

        await self.db.commit()

        await self.db.refresh(auction)

        logger.info(
            "Auction created: %s",
            auction.id,
        )

        return auction

    # ==========================================================
    # Bulk Create
    # ==========================================================

    async def bulk_create(
        self,
        auctions: list[Auction],
    ) -> list[Auction]:
        """
        Insert multiple auctions.
        """

        self.db.add_all(auctions)

        await self.db.commit()

        for auction in auctions:

            await self.db.refresh(auction)

        logger.info(
            "%d auctions inserted.",
            len(auctions),
        )

        return auctions

    # ==========================================================
    # Get Auction By ID
    # ==========================================================

    async def get_by_id(
        self,
        auction_id: str,
    ) -> Auction | None:
        """
        Get auction by id.
        """

        result = await self.db.execute(

            select(Auction).where(
                Auction.id == auction_id,
            )

        )

        return result.scalar_one_or_none()

    # ==========================================================
    # Get Auctions By Upload
    # ==========================================================

    async def get_by_upload_id(
        self,
        upload_id: str,
    ) -> list[Auction]:
        """
        Return all auctions of one upload.
        """

        result = await self.db.execute(

            select(Auction)

            .where(
                Auction.upload_id == upload_id,
            )

            .order_by(
                Auction.created_at.asc(),
            )

        )

        return list(result.scalars().all())

    # ==========================================================
    # Get All Auctions
    # ==========================================================

    async def get_all(
        self,
        limit: int = 100,
    ) -> list[Auction]:
        """
        Return all auctions.
        """

        result = await self.db.execute(

            select(Auction)

            .order_by(
                Auction.created_at.desc(),
            )

            .limit(limit)

        )

        return list(result.scalars().all())

    # ==========================================================
    # Update Auction
    # ==========================================================

    async def update(
        self,
        auction: Auction,
    ) -> Auction:
        """
        Save auction changes.
        """

        await self.db.commit()

        await self.db.refresh(auction)

        logger.info(
            "Auction updated: %s",
            auction.id,
        )

        return auction

    # ==========================================================
    # Delete Auction
    # ==========================================================

    async def delete(
        self,
        auction: Auction,
    ) -> None:
        """
        Delete auction.
        """

        await self.db.delete(auction)

        await self.db.commit()

        logger.info(
            "Auction deleted: %s",
            auction.id,
        )

    # ==========================================================
    # Delete Upload Auctions
    # ==========================================================

    async def delete_by_upload_id(
        self,
        upload_id: str,
    ) -> None:
        """
        Delete all auctions of an upload.
        """

        auctions = await self.get_by_upload_id(
            upload_id,
        )

        for auction in auctions:

            await self.db.delete(auction)

        await self.db.commit()

        logger.info(
            "Deleted %d auctions for upload %s",
            len(auctions),
            upload_id,
        )

    # ==========================================================
    # Search Borrower
    # ==========================================================

    async def search_borrower(
        self,
        borrower: str,
    ) -> list[Auction]:
        """
        Search borrower.
        """

        result = await self.db.execute(

            select(Auction).where(

                Auction.borrower.ilike(
                    f"%{borrower}%"
                )

            )

        )

        return list(result.scalars().all())

    # ==========================================================
    # Search Bank
    # ==========================================================

    async def search_bank(
        self,
        bank_name: str,
    ) -> list[Auction]:
        """
        Search bank name.
        """

        result = await self.db.execute(

            select(Auction).where(

                Auction.emd_bank_name.ilike(
                    f"%{bank_name}%"
                )

            )

        )

        return list(result.scalars().all())

    # ==========================================================
    # Count Auctions
    # ==========================================================

    async def count(
        self,
    ) -> int:
        """
        Return total auction count.
        """

        result = await self.db.execute(

            select(Auction)

        )

        return len(result.scalars().all())

    # ==========================================================
    # Exists
    # ==========================================================

    async def exists(
        self,
        auction_id: str,
    ) -> bool:
        """
        Check auction existence.
        """

        auction = await self.get_by_id(
            auction_id,
        )

        return auction is not None