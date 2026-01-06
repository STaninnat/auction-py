import uuid
from datetime import datetime
from decimal import Decimal

from models import AuctionListing, BidTransaction
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import AuthenticatedUser


class AuctionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def place_bid(self, auction_id: str, user: AuthenticatedUser, amount: Decimal) -> dict:
        """
        Thread-Safe (Concurrency Handled) Auction Function
        """

        try:
            # Start Transaction (automatically in AsyncSession)

            # Lock the auction row for update to prevent concurrent bids
            query = select(AuctionListing).where(AuctionListing.id == auction_id).with_for_update()
            result = await self.db.execute(query)
            auction = result.scalar_one_or_none()

            if not auction:
                return {"success": False, "error": "Auction not found"}

            # Validate auction status
            if auction.status != "ACTIVE":
                return {"success": False, "error": "Auction is not active"}

            if amount <= auction.current_price:
                return {
                    "success": False,
                    "error": f"Bid amount must be higher than current price {auction.current_price}",
                }

            # Update auction current price
            await self.db.execute(
                update(AuctionListing).where(AuctionListing.id == auction_id).values(current_price=amount)
            )

            # Insert new bid transaction
            new_bid_id = str(uuid.uuid4())
            await self.db.execute(
                insert(BidTransaction).values(
                    id=new_bid_id,
                    auction_id=auction_id,
                    bidder_id=user.id,
                    amount=amount,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

            # Commit Transaction
            await self.db.commit()

            return {
                "success": True,
                "bidder_id": str(user.id),
                "bidder_name": user.username or "Unknown",
                "auction_id": str(auction_id),
                "new_price": str(amount),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            await self.db.rollback()
            print(f"Error placing bid: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await self.db.close()
