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
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    return db_url


# Create engines
engine = create_engine(
    get_db_url(),
    echo=settings.DEBUG_MODE,
    pool_pre_ping=True
)

# For async operations (if needed)
if settings.DATABASE_URL.startswith("postgresql"):
    async_engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=settings.DEBUG_MODE
    )
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
else:
    async_engine = None
    AsyncSessionLocal = None

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_db():
    """Initialize database tables"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database not configured")
    
    async with AsyncSessionLocal() as session:
        yield session
