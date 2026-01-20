from config.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    # SYNC: Matches Django 'users.User' model (Explicit db_table="users")
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True)
    username = Column(String)
    email = Column(String)


class Wallet(Base):
    # SYNC: Matches Django 'payments.Wallet' model (Default: payments_wallet)
    __tablename__ = "payments_wallet"

    id = Column(UUID(as_uuid=False), primary_key=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True)
    balance = Column(Numeric(14, 2))
    held_balance = Column(Numeric(14, 2))


class AuctionListing(Base):
    # SYNC: Matches Django 'auctions.AuctionListing' model (Default: auctions_auctionlisting)
    __tablename__ = "auctions_auctionlisting"

    id = Column(UUID(as_uuid=False), primary_key=True)
    status = Column(String)
    current_price = Column(Numeric(12, 2))
    end_time = Column(DateTime)


class BidTransaction(Base):
    # SYNC: Matches Django 'auctions.BidTransaction' model (Default: auctions_bidtransaction)
    __tablename__ = "auctions_bidtransaction"

    id = Column(UUID(as_uuid=False), primary_key=True)
    amount = Column(Numeric(12, 2))
    auction_id = Column(UUID(as_uuid=False), ForeignKey("auctions_auctionlisting.id"))
    bidder_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
