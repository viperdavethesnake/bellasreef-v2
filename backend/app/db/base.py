"""
Base configuration for SQLAlchemy models.

This module provides the declarative base for all models.
The actual database engine and session management is handled in database.py.
"""

from sqlalchemy.orm import declarative_base

# Create declarative base for all models
Base = declarative_base()

# Import database components for convenience
from app.db.database import engine, AsyncSessionLocal, get_db

__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db"] 