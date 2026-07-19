import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from src.config import settings

logger = logging.getLogger(__name__)

# Initialize the async database engine
engine = create_async_engine(settings.database_url, echo=False)

# Create a configured "Session" class
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create a declarative base for models
Base = declarative_base()

async def init_db():
    """Initializes the database and automatically migrates missing columns."""
    async with engine.begin() as conn:
        # Create tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)
        
        # Safely add missing columns to the existing 'users' table (Auto-Migration)
        # IF NOT EXISTS ensures it only adds them if they are missing, preventing errors.
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR;"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;"))
        except Exception as e:
            logger.warning(f"Database migration notice (can usually be ignored): {e}")

    logger.info("Database initialized and verified successfully.")
    
