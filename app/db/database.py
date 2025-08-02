"""
Database Connection and Session Management
"""

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings
from app.db.models import Base

settings = get_settings()


def get_db_url() -> str:
    """Get database URL"""
    db_url = settings.DATABASE_URL
    
    # Ensure data directory exists for SQLite
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "")
        # Handle ./ prefix which refers to project root
        if db_path.startswith("./"):
            db_path = db_path[2:]  # Remove ./ prefix
            
        # Create parent directories if they don't exist
        parent_dir = Path(db_path).parent
        if parent_dir.name:  # Skip if it's the current directory
            parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Log the actual path being used
        from loguru import logger
        abs_path = Path(db_path).resolve().absolute()
        logger.info(f"Using database at: {abs_path}")
    
    return db_url


# Create engines
engine = create_engine(
    get_db_url(),
    echo=settings.DEBUG_MODE,
    pool_pre_ping=True
)

# For async operations (if needed) - simplified to avoid errors
async_engine = None
AsyncSessionLocal = None

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_db():
    """Initialize database tables"""
    from loguru import logger
    import time
    
    # Retry logic for database connection
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            # Create tables
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully")
            return
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"⚠️ Database connection failed (attempt {attempt}/{max_retries}): {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"❌ Failed to connect to database after {max_retries} attempts: {e}")
                logger.warning("⚠️ Continuing startup with database errors - some features may not work")
                # Don't raise - allow application to start with limited functionality


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """
    Get async database session - currently not supported
    """
    raise RuntimeError("Async database operations not configured for SQLite")
