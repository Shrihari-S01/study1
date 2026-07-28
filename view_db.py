"""
Database Inspector Utility.

Usage:
  python view_db.py               - Show database status and row counts
  python view_db.py uploads       - List all uploads
  python view_db.py auctions      - List all parsed auctions
  python view_db.py auction <id>  - Show full details of a specific auction
"""

import asyncio
import sys
from sqlalchemy import text
from app.database.connection import engine


async def get_summary():
    async with engine.connect() as conn:
        print("\n" + "=" * 60)
        print(" DATABASE STATUS & SUMMARY")
        print("=" * 60)
        print(f"Engine URL: {engine.url}")
        
        try:
            # Check uploads count
            res = await conn.execute(text("SELECT COUNT(*) FROM uploads"))
            uploads_count = res.scalar()
            print(f"Total Uploaded Newspapers : {uploads_count}")
        except Exception as e:
            print(f"Error reading uploads table: {e}")
            uploads_count = 0

        try:
            # Check auctions count
            res = await conn.execute(text("SELECT COUNT(*) FROM auctions"))
            auctions_count = res.scalar()
            print(f"Total Extracted Auctions  : {auctions_count}")
        except Exception as e:
            print(f"Error reading auctions table: {e}")
            auctions_count = 0
            
        print("=" * 60)
        print("\nQuick commands:")
        print("  python view_db.py uploads       - View all uploads")
        print("  python view_db.py auctions      - View all auctions")
        print("  python view_db.py auction <id>  - Show details of an auction")
        print("=" * 60 + "\n")


async def list_uploads():
    async with engine.connect() as conn:
        try:
            res = await conn.execute(
                text("SELECT id, upload_number, original_filename, status, total_notices, created_at FROM uploads ORDER BY created_at DESC")
            )
            rows = res.all()
            if not rows:
                print("\nNo uploads found in the database.\n")
                return

            print("\n" + "=" * 100)
            print(f"{'Upload ID / Number':<40} | {'Filename':<30} | {'Status':<12} | {'Notices':<7} | {'Created At'}")
            print("-" * 100)
            for row in rows:
                disp_name = f"{row[1]} ({row[0][:8]})"
                filename = row[2] if len(row[2]) <= 28 else row[2][:25] + "..."
                print(f"{disp_name:<40} | {filename:<30} | {row[3]:<12} | {row[4]:<7} | {row[5]}")
            print("=" * 100 + "\n")
        except Exception as e:
            print(f"Error querying uploads: {e}")


async def list_auctions():
    async with engine.connect() as conn:
        try:
            res = await conn.execute(
                text("SELECT id, borrower, asset_type, auction_start_price, confidence_score, created_at FROM auctions ORDER BY created_at DESC")
            )
            rows = res.all()
            if not rows:
                print("\nNo auction notices found in the database.\n")
                return

            print("\n" + "=" * 110)
            print(f"{'Auction ID':<10} | {'Borrower':<25} | {'Asset Type':<20} | {'Reserve Price':<15} | {'Conf':<6} | {'Created At'}")
            print("-" * 110)
            for row in rows:
                short_id = row[0][:8]
                borrower = (row[1] or "N/A") if len(row[1] or "") <= 23 else row[1][:20] + "..."
                asset_type = (row[2] or "N/A") if len(row[2] or "") <= 18 else row[2][:15] + "..."
                price = f"{row[3]:,.2f}" if row[3] is not None else "0.00"
                conf = f"{float(row[4]):.2%}" if row[4] is not None else "N/A"
                print(f"{short_id:<10} | {borrower:<25} | {asset_type:<20} | {price:>15} | {conf:<6} | {row[5]}")
            print("=" * 110 + "\n")
        except Exception as e:
            print(f"Error querying auctions: {e}")


async def show_auction(auction_id):
    async with engine.connect() as conn:
        try:
            # Try to match full ID or prefix (since we show first 8 chars in lists)
            res = await conn.execute(
                text("SELECT * FROM auctions WHERE id = :id OR id LIKE :prefix"),
                {"id": auction_id, "prefix": f"{auction_id}%"}
            )
            columns = res.keys()
            row = res.first()
            if not row:
                print(f"\nAuction with ID matching '{auction_id}' not found.\n")
                return

            print("\n" + "=" * 80)
            print(f" AUCTION RECORD DETAILS ({row[0]})")
            print("=" * 80)
            
            # Pack key-value pairs
            record = dict(zip(columns, row))
            for key, val in record.items():
                if val is not None and val != "":
                    print(f"{key:<30}: {val}")
            print("=" * 80 + "\n")
        except Exception as e:
            print(f"Error querying auction details: {e}")


async def main():
    if len(sys.argv) < 2:
        await get_summary()
    elif sys.argv[1] == "uploads":
        await list_uploads()
    elif sys.argv[1] == "auctions":
        await list_auctions()
    elif sys.argv[1] == "auction" and len(sys.argv) > 2:
        await show_auction(sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
