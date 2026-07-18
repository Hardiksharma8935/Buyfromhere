from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, BigInteger
from datetime import datetime
from src.database.core import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=True)
    balance_inr = Column(Float, default=0.0)
    balance_usd = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False, index=True)
    referred_by = Column(BigInteger, index=True, nullable=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Float, default=0.0)
    total_purchases = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price_inr = Column(Float, nullable=False)
    price_usd = Column(Float, nullable=False)
    telegram_group_id = Column(BigInteger, nullable=True) # Added dynamically by core.py
    invite_link = Column(String, nullable=True)           # Added dynamically by core.py
    is_active = Column(Boolean, default=True, index=True)

class DemoGroup(Base):
    __tablename__ = 'demo_groups'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    demo_link = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, index=True)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    method = Column(String, index=True, nullable=False)
    crypto_coin = Column(String, nullable=True)
    status = Column(String, default='Pending', index=True)
    screenshot_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
    
