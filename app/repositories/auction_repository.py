"""Auction repository."""

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction import Auction


class AuctionRepository:
    """Database operations for auctions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, auction: Auction) -> Auction:
        self.db.add(auction)
        await self.db.commit()
        await self.db.refresh(auction)
        return auction

    async def get_by_id(self, auction_id: str) -> Auction | None:
        result = await self.db.execute(select(Auction).where(Auction.id == auction_id))
        return result.scalar_one_or_none()

    async def get_by_upload_id(self, upload_id: str) -> Auction | None:
        result = await self.db.execute(select(Auction).where(Auction.upload_id == upload_id))
        return result.scalar_one_or_none()

    async def get_by_listing_id(self, listing_id: str) -> Auction | None:
        result = await self.db.execute(select(Auction).where(Auction.listing_id == listing_id))
        return result.scalar_one_or_none()

    async def list(self, search: str | None = None, limit: int = 50, offset: int = 0) -> list[Auction]:
        query: Select[tuple[Auction]] = select(Auction).order_by(Auction.created_at.desc())
        if search:
            like = f"%{search}%"
            query = query.where(
                or_(
                    Auction.listing_id.ilike(like),
                    Auction.bank_name.ilike(like),
                    Auction.borrower_name.ilike(like),
                    Auction.district.ilike(like),
                    Auction.loan_number.ilike(like),
                )
            )
        result = await self.db.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def save(self, auction: Auction) -> Auction:
        await self.db.commit()
        await self.db.refresh(auction)
        return auction

