from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.database.core import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    balance_inr = Column(Float, default=0.0)
    balance_usd = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False) # For CAPTCHA
    referred_by = Column(BigInteger, nullable=True)
    referral_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False) # 'INR' or 'USD'
    method = Column(String, nullable=False) # 'Amazon', 'Crypto', 'Stars'
    crypto_coin = Column(String, nullable=True) # 'BTC', 'USDT', etc.
    status = Column(String, default='Pending') # 'Pending', 'Approved', 'Rejected'
    screenshot_id = Column(String, nullable=True)
    from datetime import datetime
# ...
    # Remove timezone.utc
    created_at = Column(DateTime, default=datetime.utcnow)
