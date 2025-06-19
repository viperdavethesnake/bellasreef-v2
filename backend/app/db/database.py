"""
Async SQLAlchemy 2.x database configuration for Bella's Reef.

This module provides:
- Async engine creation with asyncpg
- Async session factory using async_sessionmaker
- FastAPI dependency for database sessions
- Environment-aware connection pooling
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Database URL with asyncpg driver
DATABASE_URL = str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")

# Engine configuration based on environment
if settings.ENV == "development":
    # Development: Simple configuration with NullPool for easier debugging
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool,
    )
else:
    # Production: Full connection pooling for performance and reliability
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_timeout=30,
    )

# Async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Disable autoflush for better performance and explicit control
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Provides an async session with automatic cleanup and error handling.
    Sessions are automatically closed when the request completes.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# Export for convenience
__all__ = ["engine", "async_session", "get_db"] 