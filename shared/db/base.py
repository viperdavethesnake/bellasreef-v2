"""
Database base configuration and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database components from the main database module
from shared.db.database import engine, async_session, get_db, Base

__all__ = ["Base", "engine", "async_session", "get_db"] 