#!/usr/bin/env python3
"""
Database initialization script for Bella's Reef.
Drops and recreates the database schema and adds a default admin user.
Uses Pydantic v2 settings for configuration.
"""

import asyncio
import sys
from pathlib import Path

# --- Ensure backend is on the Python path ---
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import after adding to path
from app.core.config import settings
from app.db.base import engine, AsyncSessionLocal, Base
from app.db.models import User
from app.core.security import get_password_hash

async def reset_db():
    """
    Drop and recreate all database tables.
    Uses async SQLAlchemy engine from app.db.base.
    """
    async with engine.begin() as conn:
        print("📛 Dropping existing database schema...")
        await conn.run_sync(Base.metadata.drop_all)
        print("📐 Creating new database schema...")
        await conn.run_sync(Base.metadata.create_all)

async def create_admin_user():
    """
    Create default admin user using settings from .env file.
    Uses Pydantic v2 settings for admin credentials.
    """
    async with AsyncSessionLocal() as session:
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            phone_number=settings.ADMIN_PHONE,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            is_active=True,
            is_admin=True
        )
        session.add(admin)
        await session.commit()
        print(f"👤 Admin user '{settings.ADMIN_USERNAME}' created.")

async def main():
    """
    Main function to initialize database and create admin user.
    """
    print(f"🔧 Initializing database: {settings.DATABASE_URL}")
    await reset_db()
    await create_admin_user()
    print("✅ Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(main())

