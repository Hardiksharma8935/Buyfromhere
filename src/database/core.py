import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, select
from src.config import settings

logger = logging.getLogger(__name__)

# Connection Pooling Optimized for Railway
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800, # Recycle connections every 30 minutes to prevent stale drops
    pool_pre_ping=True, # Verify connection health before usage
    echo=False
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def run_auto_migrations(conn):
    """Zero-touch migration system for Railway to fix missing columns."""
    logger.info("Checking database schema for missing columns...")
    
    # Check for referral_earnings in users
    res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='referral_earnings';"))
    if not res.fetchone():
        await conn.execute(text("ALTER TABLE users ADD COLUMN referral_earnings FLOAT DEFAULT 0.0;"))
        logger.info("Migrated: Added referral_earnings to users")

    # Check for total_purchases in users
    res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='total_purchases';"))
    if not res.fetchone():
        await conn.execute(text("ALTER TABLE users ADD COLUMN total_purchases INTEGER DEFAULT 0;"))
        logger.info("Migrated: Added total_purchases to users")

    # Check for telegram_group_id in groups
    res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='groups' AND column_name='telegram_group_id';"))
    if not res.fetchone():
        await conn.execute(text("ALTER TABLE groups ADD COLUMN telegram_group_id BIGINT;"))
        logger.info("Migrated: Added telegram_group_id to groups")

    # Check for invite_link in groups
    res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='groups' AND column_name='invite_link';"))
    if not res.fetchone():
        await conn.execute(text("ALTER TABLE groups ADD COLUMN invite_link VARCHAR;"))
        logger.info("Migrated: Added invite_link to groups")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_auto_migrations(conn)
        
    # Seed default settings safely
    async with AsyncSessionLocal() as session:
        from src.database.models import Setting
        defaults = {
            "BTC_ADDRESS": "your_btc_wallet_here",
            "ETH_ADDRESS": "your_eth_wallet_here",
            "SOL_ADDRESS": "your_sol_wallet_here",
            "USDT_ADDRESS": "your_usdt_wallet_here",
            "MAIN_CHANNEL_LINK": "https://t.me/telegram",
            "AMAZON_MIN_DEPOSIT": "100"
        }
        for key, val in defaults.items():
            result = await session.execute(select(Setting).where(Setting.key == key))
            if not result.scalar_one_or_none():
                session.add(Setting(key=key, value=val))
        await session.commit()
        
