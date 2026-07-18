from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import select
from src.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed default settings if they don't exist
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
        
