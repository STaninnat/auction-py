import uuid
from datetime import datetime
from decimal import Decimal

from models import AuctionListing, BidTransaction, Wallet
from sqlalchemy import insert, select
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

            # 1. Lock the wallet FIRST (to avoid deadlocks, order matters if multiple resources)
            # We want to ensure user has money.
            query_wallet = select(Wallet).where(Wallet.user_id == user.id).with_for_update()
            result_wallet = await self.db.execute(query_wallet)
            wallet = result_wallet.scalar_one_or_none()

            if not wallet:
                return {"success": False, "error": "Wallet not found"}

            if wallet.balance < amount:
                return {"success": False, "error": f"Insufficient funds. Balance: {wallet.balance}"}

            # 2. Lock the auction
            query_auction = select(AuctionListing).where(AuctionListing.id == auction_id).with_for_update()
            result_auction = await self.db.execute(query_auction)
            auction = result_auction.scalar_one_or_none()

            if not auction:
                return {"success": False, "error": "Auction not found"}

            # Validate auction status
            if auction.status != "ACTIVE":
                return {"success": False, "error": "Auction is not active"}

            if datetime.utcnow() > auction.end_time.replace(tzinfo=None):
                return {"success": False, "error": "Auction has expired"}

            if amount <= auction.current_price:
                return {
                    "success": False,
                    "error": f"Bid amount must be higher than current price {auction.current_price}",
                }

            # 3. Deduct Money & Hold
            wallet.balance -= amount
            wallet.held_balance += amount
            # Direct object update works in SQLAlchemy session

            # 4. Update Auction
            auction.current_price = amount

            # 5. Insert Bid
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
                "new_balance": str(wallet.balance),  # Return new balance for private ACK
            }

        except Exception as e:
            await self.db.rollback()
            print(f"Error placing bid: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await self.db.close()
