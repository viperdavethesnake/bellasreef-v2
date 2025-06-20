#!/usr/bin/env python3
"""
Database initialization script for Bella's Reef.

IMPROVEMENTS:
- Robust error checking for missing core/.env file and required settings
- CLI flags for dry-run and configuration checking
- Flexible path handling (runs from project root or scripts directory)
- Clear user feedback with status icons and messages
- Proper exit codes for error conditions
- Async operation with Pydantic v2 settings
- Comprehensive validation before database operations
- Complete PostgreSQL schema reset using DROP SCHEMA public CASCADE

USAGE:
    python scripts/init_db.py          # Normal initialization
    python scripts/init_db.py --check  # Validate config only
    python scripts/init_db.py --dry-run # Check config and print summary
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

# Debug: Print tables before model imports
print("[DEBUG] Tables registered BEFORE model imports:", list(Base.metadata.tables.keys()))

from shared.db.models import (
    User, Device, History, Alert, AlertEvent, 
    Schedule, DeviceAction, Probe, ProbeHistory
)
from shared.core.security import get_password_hash
from shared.crud.user import get_user_by_username
from smartoutlets.models import SmartOutlet

# Debug: Print tables after all model imports
print("[DEBUG] Tables registered AFTER model imports:", list(Base.metadata.tables.keys()))

from sqlalchemy import text

def check_env_file() -> bool:
    """Check if core/.env file exists and print status."""
    env_path = project_root / "core" / ".env"
    if not env_path.exists():
        print("❌ Error: core/.env file not found!")
        print(f"   Expected location: {env_path}")
        print("   Please copy core/env.example to core/.env and configure your settings.")
        print("   Then run: python3 $SCRIPT_DIR/init_db.py")
        return False
    
    print(f"✅ Found core/.env file: {env_path}")
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
        if not value or value.strip() == "":
            missing_settings.append(name)
    
    if missing_settings:
        print("❌ Error: Missing required settings in core/.env file:")
        for setting in missing_settings:
            print(f"   - {setting}")
        print("   Please check your core/.env file and ensure all required values are set.")
        return False
    
    print("✅ All required settings are configured.")
    return True

def print_config_summary():
    """Print a summary of the current configuration."""
    print("\n📋 Configuration Summary:")
    print(f"   Database URL: {settings.DATABASE_URL}")
    print(f"   Admin User: {settings.ADMIN_USERNAME} ({settings.ADMIN_EMAIL})")
    print(f"   Service Token: {settings.SERVICE_TOKEN[:10]}...")
    print(f"   Service Port: {settings.SERVICE_PORT}")
    print(f"   Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

async def reset_db():
    """
    Completely reset the PostgreSQL database schema.
    
    This function performs a complete schema reset by:
    1. Dropping the entire 'public' schema with CASCADE (removes all tables, constraints, sequences, etc.)
    2. Recreating the 'public' schema
    3. Creating all tables using SQLAlchemy Base.metadata.create_all
    
    This ensures a complete, dependency-safe reset regardless of foreign key constraints.
    """
    try:
        async with engine.begin() as conn:
            print("🗑️  Dropping entire 'public' schema with CASCADE...")
            print("   This will remove ALL tables, constraints, sequences, and dependent objects.")
            
            # Drop the entire public schema with CASCADE
            # This removes all tables, constraints, sequences, functions, etc. regardless of dependencies
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            print("✅ Public schema dropped successfully.")
            
            print("🏗️  Recreating 'public' schema...")
            # Recreate the public schema
            await conn.execute(text("CREATE SCHEMA public"))
            print("✅ Public schema recreated successfully.")
            
            print("📐 Creating all database tables...")
            # Debug: Print before table creation
            print("[DEBUG] Creating tables with create_all...")
            # Create all tables using SQLAlchemy metadata
            # This includes all probe-related tables for the temperature service (probes, probe_history)
            await conn.run_sync(Base.metadata.create_all)
            print("[DEBUG] Tables created!")
            print("✅ All database tables created successfully.")
            
        print("✅ Database schema reset complete.")
        print("   All tables, constraints, and sequences have been recreated from scratch.")
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        print("   This may indicate a connection issue or insufficient database privileges.")
        print("   Ensure PostgreSQL is running and the database user has CREATE/DROP privileges.")
        raise

async def create_admin_user():
    """
    Create default admin user using settings from .env file.
    Uses Pydantic v2 settings for admin credentials.
    """
    try:
        async with async_session() as session:
            # Check if admin user already exists
            existing_admin = await get_user_by_username(session, settings.ADMIN_USERNAME)
            if existing_admin:
                print(f"⚠️  Admin user '{settings.ADMIN_USERNAME}' already exists.")
                return
            
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                phone_number="",  # Optional field, leave empty
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
    """
    Main function to initialize database and create admin user.
    """
    parser = argparse.ArgumentParser(description="Initialize Bella's Reef database")
    parser.add_argument("--check", action="store_true", help="Validate configuration only")
    parser.add_argument("--dry-run", action="store_true", help="Check config and print summary")
    
    args = parser.parse_args()
    
    print("🗄️  Bella's Reef Database Initialization")
    print("=" * 50)
    
    # Check .env file
    if not check_env_file():
        sys.exit(1)
    
    # Validate required settings
    if not validate_required_settings():
        sys.exit(1)
    
    # Print configuration summary
    print_config_summary()
    
    # Handle CLI flags
    if args.check:
        print("\n✅ Configuration validation complete.")
        return
    
    if args.dry_run:
        print("\n✅ Dry run complete. No database changes made.")
        return
    
    # Confirm before proceeding with database changes
    print(f"\n⚠️  DESTRUCTIVE OPERATION WARNING!")
    print(f"   This will COMPLETELY RESET the database schema:")
    print(f"   - DROP SCHEMA public CASCADE (removes ALL data)")
    print(f"   - CREATE SCHEMA public (recreates empty schema)")
    print(f"   - Recreate all tables from scratch")
    print(f"   - All existing data will be PERMANENTLY LOST")
    print(f"")
    print(f"   Database: {settings.DATABASE_URL}")
    print(f"")
    
    response = input("   Continue with schema reset? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Database initialization cancelled.")
        sys.exit(0)
    
    try:
        print("\n🔄 Starting complete database schema reset...")
        await reset_db()
        await create_admin_user()
        print("\n🎉 Database initialization complete!")
        print("   Database schema has been completely reset and recreated.")
        print("   Admin user has been created with credentials from .env file.")
        print("   You can now start the application with: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        print("   Please check your database connection and permissions.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

