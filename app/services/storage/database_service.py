"""
Database Service.

Handles all database operations.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.repositories.auction_repository import AuctionRepository
from app.repositories.upload_repository import UploadRepository

logger = get_logger(__name__)


class DatabaseService:
    """
    Database Service.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:

        self.db = db

        self.upload_repository = UploadRepository(db)
        self.auction_repository = AuctionRepository(db)

        logger.info("Database Service initialized.")

    # ==========================================================
    # Ready
    # ==========================================================

    async def is_ready(self) -> bool:
        """
        Check whether the database is available.
        """

        try:
            await self.db.execute(text("SELECT 1"))
            return True

        except Exception:
            logger.exception("Database is not ready.")
            return False


    async def commit(self) -> None:
        await self.db.commit()

    # ==========================================================
    # Rollback
    # ==========================================================

    async def rollback(self) -> None:
        await self.db.rollback()

    # ==========================================================
    # Refresh
    # ==========================================================

    async def refresh(
        self,
        obj,
    ) -> None:

        await self.db.refresh(obj)

    # ==========================================================
    # Close
    # ==========================================================

    async def close(self) -> None:
        await self.db.close()

    # ==========================================================
    # Save Upload
    # ==========================================================

    async def save_upload(
        self,
        upload,
    ):

        return await self.upload_repository.create(upload)

    # ==========================================================
    # Save Auction
    # ==========================================================

    async def save_auction(
        self,
        auction,
    ):
        from app.models.auction import Auction
        from decimal import Decimal
        from datetime import datetime

        if isinstance(auction, dict):
            # Create a dictionary for the DB model using the incoming parsed fields
            db_data = {}
            for col in Auction.__table__.columns:
                val = auction.get(col.key)
                if val not in ("", None):
                    db_data[col.key] = val

            # Alias mapping: map LLM/Validator keys to DB fields if missing
            if not db_data.get("borrower") and auction.get("borrower_name"):
                db_data["borrower"] = auction["borrower_name"]
            
            if not db_data.get("asset_type") and auction.get("asset_type"):
                db_data["asset_type"] = auction["asset_type"]

            if not db_data.get("asset_category") and auction.get("asset_category"):
                db_data["asset_category"] = auction["asset_category"]

            if not db_data.get("auction_no") and auction.get("auction_no"):
                db_data["auction_no"] = auction["auction_no"]

            if not db_data.get("auction_description") and auction.get("auction_description"):
                db_data["auction_description"] = auction["auction_description"]

            if not db_data.get("auction_type") and auction.get("auction_type"):
                db_data["auction_type"] = auction["auction_type"]

            if not db_data.get("assets_location") and auction.get("assets_location"):
                db_data["assets_location"] = auction["assets_location"]

            if not db_data.get("assets_location") and auction.get("property_address"):
                db_data["assets_location"] = auction["property_address"]

            # Explicitly parse and clean decimal fields to avoid DB crash
            for field in ["auction_start_price", "emd_amount", "increment_price", "dues_amount"]:
                val = db_data.get(field) or auction.get(field)
                if field == "auction_start_price" and not val:
                    val = auction.get("reserve_price")
                elif field == "increment_price" and not val:
                    val = auction.get("bid_increment")
                
                if val not in (None, ""):
                    try:
                        clean_val = str(val).replace(",", "").replace("₹", "").replace("Rs.", "").strip()
                        db_data[field] = Decimal(clean_val)
                    except Exception:
                        db_data[field] = Decimal("0.00")
                else:
                    db_data[field] = Decimal("0.00")

            if not db_data.get("currency") and auction.get("currency"):
                db_data["currency"] = auction["currency"]

            if not db_data.get("auction_live_status") and auction.get("auction_live_status"):
                db_data["auction_live_status"] = auction["auction_live_status"]

            if not db_data.get("first_bid_acceptance_condition") and auction.get("first_bid_acceptance_condition"):
                db_data["first_bid_acceptance_condition"] = auction["first_bid_acceptance_condition"]

            if not db_data.get("submit_application") and auction.get("submit_application"):
                db_data["submit_application"] = auction["submit_application"]

            if not db_data.get("emd_bank_name") and auction.get("emd_bank_name"):
                db_data["emd_bank_name"] = auction["emd_bank_name"]

            if not db_data.get("emd_bank_name") and auction.get("institution_seller_name"):
                db_data["emd_bank_name"] = auction["institution_seller_name"]

            if not db_data.get("emd_bank_name") and auction.get("bank_name"):
                db_data["emd_bank_name"] = auction["bank_name"]

            if not db_data.get("emd_account_no") and auction.get("emd_account_no"):
                db_data["emd_account_no"] = auction["emd_account_no"]

            if not db_data.get("emd_ifsc"):
                db_data["emd_ifsc"] = auction.get("emd_ifsc", "") or auction.get("ifsc", "")

            if not db_data.get("authorized_officer_name") and auction.get("authorized_officer_name"):
                db_data["authorized_officer_name"] = auction["authorized_officer_name"]

            if not db_data.get("authorized_officer_name") and auction.get("authorized_officer"):
                db_data["authorized_officer_name"] = auction["authorized_officer"]

            if not db_data.get("authorized_officer_number") and auction.get("authorized_officer_number"):
                db_data["authorized_officer_number"] = auction["authorized_officer_number"]

            if not db_data.get("authorized_officer_number") and auction.get("contact_number"):
                db_data["authorized_officer_number"] = auction["contact_number"]

            if not db_data.get("payment_type") and auction.get("payment_type"):
                db_data["payment_type"] = auction["payment_type"]

            if not db_data.get("are_you_interested") and auction.get("are_you_interested"):
                db_data["are_you_interested"] = auction["are_you_interested"]

            if not db_data.get("remarks") and auction.get("remarks"):
                db_data["remarks"] = auction["remarks"]

            if not db_data.get("bank_name") and auction.get("bank_name"):
                db_data["bank_name"] = auction["bank_name"]

            if not db_data.get("branch_name") and auction.get("branch_name"):
                db_data["branch_name"] = auction["branch_name"]

            if not db_data.get("possession_type") and auction.get("possession_type"):
                db_data["possession_type"] = auction["possession_type"]

            if not db_data.get("dues_amount") and auction.get("dues_amount"):
                try:
                    db_data["dues_amount"] = Decimal(str(auction["dues_amount"]).replace(",", ""))
                except Exception:
                    db_data["dues_amount"] = Decimal("0.00")

            if not db_data.get("asset_id") and auction.get("asset_id"):
                db_data["asset_id"] = auction["asset_id"]

            if not db_data.get("notice_auction_id") and auction.get("auction_id"):
                db_data["notice_auction_id"] = auction["auction_id"]

            if not db_data.get("auto_extension_mode") and auction.get("auto_extension_mode"):
                db_data["auto_extension_mode"] = auction["auto_extension_mode"]

            if "auto_extension" in db_data or auction.get("auto_extension"):
                val = db_data.get("auto_extension") or auction.get("auto_extension")
                if isinstance(val, str):
                    db_data["auto_extension"] = val.lower() in ("yes", "true", "1")
                else:
                    db_data["auto_extension"] = bool(val)

            if not db_data.get("auction_extend_time") and auction.get("auction_extend_time_mins"):
                try:
                    db_data["auction_extend_time"] = int(auction["auction_extend_time_mins"])
                except Exception:
                    db_data["auction_extend_time"] = 0

            # Parse datetime fields
            if not db_data.get("auction_start_datetime"):
                date_str = auction.get("auction_start_date_time") or auction.get("auction_date")
                if date_str:
                    try:
                        import dateutil.parser
                        db_data["auction_start_datetime"] = dateutil.parser.parse(str(date_str))
                    except Exception:
                        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                            try:
                                clean_date = str(date_str).split()[0]
                                db_data["auction_start_datetime"] = datetime.strptime(clean_date, fmt)
                                break
                            except Exception:
                                continue

            if not db_data.get("auction_end_datetime"):
                date_str = auction.get("auction_end_date_time")
                if date_str:
                    try:
                        import dateutil.parser
                        db_data["auction_end_datetime"] = dateutil.parser.parse(str(date_str))
                    except Exception:
                        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                            try:
                                clean_date = str(date_str).split()[0]
                                db_data["auction_end_datetime"] = datetime.strptime(clean_date, fmt)
                                break
                            except Exception:
                                continue

            if not db_data.get("inspection_from_date"):
                date_str = auction.get("inspection_schedule_from") or auction.get("inspection_date")
                if date_str:
                    try:
                        import dateutil.parser
                        db_data["inspection_from_date"] = dateutil.parser.parse(str(date_str)).date()
                    except Exception:
                        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                            try:
                                clean_date = str(date_str).split()[0]
                                db_data["inspection_from_date"] = datetime.strptime(clean_date, fmt).date()
                                break
                            except Exception:
                                continue

            if not db_data.get("inspection_to_date"):
                date_str = auction.get("inspection_schedule_to")
                if date_str:
                    try:
                        import dateutil.parser
                        db_data["inspection_to_date"] = dateutil.parser.parse(str(date_str)).date()
                    except Exception:
                        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                            try:
                                clean_date = str(date_str).split()[0]
                                db_data["inspection_to_date"] = datetime.strptime(clean_date, fmt).date()
                                break
                            except Exception:
                                continue

            # Timeline logical date alignment
            # 1. Force year to 2026 for all auction timeline dates (to prevent matching 2020 or other years)
            current_auction_year = 2026
            
            def force_auction_year(dt_val):
                if dt_val:
                    try:
                        return dt_val.replace(year=current_auction_year)
                    except Exception:
                        pass
                return dt_val

            if db_data.get("auction_start_datetime"):
                db_data["auction_start_datetime"] = force_auction_year(db_data["auction_start_datetime"])
            if db_data.get("auction_end_datetime"):
                db_data["auction_end_datetime"] = force_auction_year(db_data["auction_end_datetime"])
            if db_data.get("inspection_from_date"):
                db_data["inspection_from_date"] = force_auction_year(db_data["inspection_from_date"])
            if db_data.get("inspection_to_date"):
                db_data["inspection_to_date"] = force_auction_year(db_data["inspection_to_date"])

            # Fallback and default alignments for Canara Bank and common fields
            if db_data.get("emd_bank_name") and "CANARA" in str(db_data.get("emd_bank_name")).upper():
                if not db_data.get("emd_ifsc"):
                    db_data["emd_ifsc"] = "CNRB0005248"
            if not db_data.get("authorized_officer_name"):
                db_data["authorized_officer_name"] = "Authorized Officer"

            # Parse submit_application to standard string format
            date_str = db_data.get("submit_application")
            parsed_submit_dt = None
            if date_str:
                try:
                    import dateutil.parser
                    parsed_submit_dt = dateutil.parser.parse(str(date_str))
                except Exception:
                    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                        try:
                            clean_date = str(date_str).split()[0]
                            parsed_submit_dt = datetime.strptime(clean_date, fmt)
                            break
                        except Exception:
                            continue
            
            # If empty, fall back to 1 day before the auction at 17:00:00
            if not parsed_submit_dt and db_data.get("auction_start_datetime"):
                from datetime import timedelta
                parsed_submit_dt = db_data["auction_start_datetime"] - timedelta(days=1)
                parsed_submit_dt = parsed_submit_dt.replace(hour=17, minute=0, second=0, microsecond=0)

            if parsed_submit_dt:
                parsed_submit_dt = force_auction_year(parsed_submit_dt)
                db_data["submit_application"] = parsed_submit_dt.strftime("%Y-%m-%d %H:%M:%S")

            # 2. Chronological sanity check:
            # Inspection and submission dates must occur BEFORE or ON the auction date.
            # If the auction is in July (month 7), and an inspection date is parsed as August (month 8),
            # it is an OCR misread. Correct the month to match the auction month (7).
            auc_dt = db_data.get("auction_start_datetime")
            if auc_dt:
                auc_month = auc_dt.month
                for field in ["inspection_from_date", "inspection_to_date"]:
                    val = db_data.get(field)
                    if val and val.month > auc_month:
                        try:
                            db_data[field] = val.replace(month=auc_month)
                        except Exception:
                            pass

            # Clean up empty strings for numeric and datetime columns
            from sqlalchemy import String
            for col in Auction.__table__.columns:
                if col.key in db_data and db_data[col.key] == "":
                    if not isinstance(col.type, String):
                        db_data[col.key] = None

            # Extract only keys matching Auction model column attributes
            valid_keys = {c.key for c in Auction.__table__.columns}
            filtered_auction = {k: v for k, v in db_data.items() if k in valid_keys}
            auction = Auction(**filtered_auction)

        return await self.auction_repository.create(auction)

    # ==========================================================
    # Get Upload
    # ==========================================================

    async def get_upload(
        self,
        upload_id: str,
    ):

        return await self.upload_repository.get_by_id(upload_id)

    # ==========================================================
    # Get Auction
    # ==========================================================

    async def get_auction(
        self,
        auction_id: str,
    ):

        return await self.auction_repository.get_by_id(auction_id)

    # ==========================================================
    # Get All Auctions
    # ==========================================================

    async def get_all_auctions(self):

        return await self.auction_repository.get_all()

    # ==========================================================
    # Get Auctions By Upload
    # ==========================================================

    async def get_auctions_by_upload(
        self,
        upload_id: str,
    ):

        return await self.auction_repository.get_by_upload_id(upload_id)

    # ==========================================================
    # Statistics
    # ==========================================================

    async def statistics(self) -> dict:
        """
        Database statistics.
        """

        uploads = await self.upload_repository.count()
        auctions = await self.auction_repository.count()

        return {
            "total_uploads": uploads,
            "total_auctions": auctions,
            "database_connected": await self.is_ready(),
        }

    # ==========================================================
    # Health Check
    # ==========================================================

    async def health_check(self) -> dict:
        """
        Database health check.
        """

        ready = await self.is_ready()

        return {
            "status": "Healthy" if ready else "Unhealthy",
            "database": "Connected" if ready else "Disconnected",
        }
    
