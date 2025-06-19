"""
Async SQLAlchemy 2.x database configuration for Bella's Reef.

This module provides:
- Async engine creation with asyncpg
- Async session factory using async_sessionmaker
- FastAPI dependency for database sessions
- Proper connection pooling and error handling
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Create async engine with proper configuration
engine = create_async_engine(
    # Convert postgresql:// to postgresql+asyncpg:// for async support
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"),
    
    # Engine configuration
    echo=settings.DEBUG,  # SQL logging in debug mode
    future=True,  # Use SQLAlchemy 2.x features
    
    # Connection pooling (disabled for development, enabled for production)
    poolclass=NullPool if settings.ENV == "development" else None,
    pool_size=10 if settings.ENV != "development" else None,
    max_overflow=20 if settings.ENV != "development" else None,
    pool_pre_ping=True,  # Validate connections before use
    
    # Performance settings
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Wait up to 30 seconds for a connection
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
    autoflush=True,  # Auto-flush changes
    autocommit=False,  # Use explicit transactions
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    This is an async generator that yields database sessions.
    It properly handles session lifecycle and cleanup.
    
    Usage in FastAPI endpoints:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # Rollback on any exception
            await session.rollback()
            raise
        finally:
            # Session is automatically closed by async context manager
            pass

# Export for convenience
__all__ = ["engine", "AsyncSessionLocal", "get_db"] 