from config.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    __tablename__ = "users_user"

    id = Column(UUID(as_uuid=False), primary_key=True)
    username = Column(String)
    email = Column(String)


class AuctionListing(Base):
    __tablename__ = "auctions_auctionlisting"

    id = Column(UUID(as_uuid=False), primary_key=True)
    status = Column(String)
    current_price = Column(Numeric(12, 2))


class BidTransaction(Base):
    __tablename__ = "auctions_bidtransaction"

    id = Column(UUID(as_uuid=False), primary_key=True)
    amount = Column(Numeric(12, 2))
    auction_id = Column(UUID(as_uuid=False), ForeignKey("auctions_auctionlisting.id"))
    bidder_id = Column(UUID(as_uuid=False), ForeignKey("users_user.id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
