from sqlalchemy import Column, BigInteger, String, Float, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from src.database.core import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    
    balance_inr = Column(Float, default=0.0)
    balance_usd = Column(Float, default=0.0)
    
    # Restored missing verification and referral columns
    is_verified = Column(Boolean, default=False, index=True)
    referred_by = Column(BigInteger, index=True, nullable=True)
    
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Float, default=0.0)
    total_purchases = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    amount = Column(Float)
    currency = Column(String)
    method = Column(String)
    crypto_coin = Column(String, nullable=True)
    screenshot_id = Column(String, nullable=True)
    status = Column(String, default="Pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
