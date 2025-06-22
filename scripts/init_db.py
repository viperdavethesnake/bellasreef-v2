#!/usr/bin/env python3
"""
Database initialization script for Bella's Reef. (v2)

This script is updated to work with the unified project structure,
loading configuration from a single .env file at the project root.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from shared.core.config import settings
from shared.db.database import engine, async_session, Base
from shared.db.models import (
    User, Device, Alert, DeviceAction, History, SmartOutlet, VeSyncAccount
)
from shared.core.security import get_password_hash
from shared.crud.user import get_user_by_username
from sqlalchemy import text

def check_env_file() -> bool:
    """Check if the root .env file exists and print status."""
    # This now correctly points to the project root .env file.
    env_path = project_root / ".env"
    if not env_path.exists():
        print("❌ Error: Project root .env file not found!")
        print(f"   Expected location: {env_path}")
        print("   Please copy env.example to .env and configure your settings.")
        return False
    
    print(f"✅ Found project .env file: {env_path}")
    return True

def validate_required_settings() -> bool:
    """Validate that all required settings are present."""
    required_settings = {
        "SECRET_KEY": settings.SECRET_KEY,
        "DATABASE_URL": settings.DATABASE_URL,
        "SERVICE_TOKEN": settings.SERVICE_TOKEN,
        "ADMIN_USERNAME": settings.ADMIN_USERNAME,
        "ADMIN_PASSWORD": settings.ADMIN_PASSWORD,
        "ADMIN_EMAIL": settings.ADMIN_EMAIL,
    }
    
    missing_settings = []
    for name, value in required_settings.items():
        if not value or "changeme" in value or "your_secure_password" in value:
            missing_settings.append(name)
    
    if missing_settings:
        # Corrected error message to refer to the root .env file.
        print("❌ Error: Missing or default required settings in your .env file:")
        for setting in missing_settings:
            print(f"   - {setting}")
        print("   Please check your .env file and ensure all required values are set.")
        return False
    
    print("✅ All required settings are configured.")
    return True

def print_config_summary():
    """Print a summary of the current configuration."""
    print("\n📋 Configuration Summary:")
    print(f"   Database URL:   {settings.DATABASE_URL}")
    print(f"   Admin User:     {settings.ADMIN_USERNAME} ({settings.ADMIN_EMAIL})")
    print(f"   Service Token:  {settings.SERVICE_TOKEN[:10]}...")
    # Updated to show multiple service ports for clarity
    print("   Service Ports:")
    print(f"     - Core:         {settings.SERVICE_PORT_CORE}")
    print(f"     - Temp:         {settings.SERVICE_PORT_TEMP}")
    print(f"     - SmartOutlets: {settings.SERVICE_PORT_SMARTOUTLETS}")

async def reset_db():
    """Completely reset the PostgreSQL database schema."""
    try:
        async with engine.begin() as conn:
            print("\n🗑️  Dropping entire 'public' schema with CASCADE...")
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            print("✅ Public schema dropped successfully.")
            
            print("🏗️  Recreating 'public' schema...")
            await conn.execute(text("CREATE SCHEMA public"))
            print("✅ Public schema recreated successfully.")
            
            print("📐 Creating all database tables from unified models...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All database tables created successfully.")
            
        print("\n✅ Database schema reset complete.")
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        print("   This may indicate a connection issue or insufficient database privileges.")
        print("   Ensure PostgreSQL is running and the database user has CREATE/DROP privileges.")
        raise

async def create_admin_user():
    """Create default admin user using settings from .env file."""
    try:
        async with async_session() as session:
            existing_admin = await get_user_by_username(session, settings.ADMIN_USERNAME)
            if existing_admin:
                print(f"⚠️  Admin user '{settings.ADMIN_USERNAME}' already exists.")
                return
            
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                phone_number="",
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_admin=True
            )
            session.add(admin)
            await session.commit()
            print(f"👤 Admin user '{settings.ADMIN_USERNAME}' created successfully.")
    except Exception as e:
        print(f"❌ Admin user creation failed: {e}")
        raise

async def main():
    """Main function to initialize database and create admin user."""
    parser = argparse.ArgumentParser(description="Initialize Bella's Reef database")
    parser.add_argument("--check", action="store_true", help="Validate configuration only")
    parser.add_argument("--dry-run", action="store_true", help="Check config and print summary")
    
    args = parser.parse_args()
    
    print("🗄️  Bella's Reef Database Initialization")
    print("=" * 50)
    
    if not check_env_file():
        sys.exit(1)
    
    if not validate_required_settings():
        sys.exit(1)
    
    print_config_summary()
    
    if args.check or args.dry_run:
        print("\n✅ Dry run complete. No database changes made.")
        return
    
    print(f"\n⚠️  DESTRUCTIVE OPERATION WARNING!")
    print(f"   This will COMPLETELY RESET the database at:")
    print(f"   -> {settings.DATABASE_URL}")
    print(f"   All existing data in the 'public' schema will be PERMANENTLY LOST.")
    
    response = input("\n   Continue with schema reset? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Database initialization cancelled.")
        sys.exit(0)
    
    try:
        await reset_db()
        await create_admin_user()
        print("\n🎉 Database initialization complete!")
        print("   You can now start the application services.")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed during execution.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
