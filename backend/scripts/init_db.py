#!/usr/bin/env python3
"""
Database initialization script for Bella's Reef.
Drops and recreates the database schema and adds a default admin user.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# --- Ensure backend is on the Python path ---
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.db.base import async_engine, async_session
from app.db.models import Base, User
from app.core.security import get_password_hash

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "reefrocks")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+15555555555")

async def reset_db():
    async with async_engine.begin() as conn:
        print("📛 Dropping existing database schema...")
        await conn.run_sync(Base.metadata.drop_all)
        print("📐 Creating new database schema...")
        await conn.run_sync(Base.metadata.create_all)

async def create_admin_user():
    async with async_session() as session:
        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            phone_number=ADMIN_PHONE,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            is_active=True,
            is_admin=True
        )
        session.add(admin)
        await session.commit()
        print(f"👤 Admin user '{ADMIN_USERNAME}' created.")

async def main():
    await reset_db()
    await create_admin_user()
    print("✅ Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(main())

