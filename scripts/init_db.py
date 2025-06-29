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
    User, Device, Alert, DeviceAction, History, HistoryHourlyAggregate, SmartOutlet, VeSyncAccount
)
from lighting.db.models import LightingBehavior, LightingGroup, LightingBehaviorAssignment, LightingBehaviorLog
from shared.core.security import get_password_hash
from shared.crud.user import get_user_by_username
from lighting.services.crud import lighting_behavior
from lighting.models.schemas import LightingBehaviorCreate, LightingBehaviorType
from sqlalchemy import text

# ANSI Color Constants
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
NC = "\033[0m"  # No Color

def print_banner():
    """Print the Bella's Reef banner."""
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════════╗
║                    {BOLD}🗄️  Bella's Reef v2.3.0{NC}{BLUE}                    ║
║                   Database Initialization                    ║
╚══════════════════════════════════════════════════════════════╝{NC}
""")

def print_section(title: str):
    """Print a section header."""
    print(f"\n{BLUE}╔══ {BOLD}{title}{NC}{BLUE} {'═' * (50 - len(title))}")

def print_section_end():
    """Print a section end."""
    print(f"{BLUE}╚{'═' * 52}{NC}\n")

def print_progress(message: str):
    """Print a progress message."""
    print(f"{BLUE}🔄{NC} {BOLD}{message}{NC}")

def print_success(message: str):
    """Print a success message."""
    print(f"{GREEN}✓{NC} {BOLD}{message}{NC}")

def print_error(message: str):
    """Print an error message."""
    print(f"{RED}✗{NC} {BOLD}{message}{NC}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠️{NC} {BOLD}{message}{NC}")

def print_info(message: str):
    """Print an info message."""
    print(f"{CYAN}ℹ️{NC} {BOLD}{message}{NC}")

def check_env_file() -> bool:
    """Check if the root .env file exists and print status."""
    print_section("Environment Check")
    
    # This now correctly points to the project root .env file.
    env_path = project_root / ".env"
    if not env_path.exists():
        print_error("Project root .env file not found!")
        print(f"   {CYAN}Expected location:{NC} {env_path}")
        print(f"   {WHITE}Please copy env.example to .env and configure your settings.{NC}")
        return False
    
    print_success("Found project .env file")
    print(f"   {CYAN}Location:{NC} {env_path}")
    return True

def validate_required_settings() -> bool:
    """Validate that all required settings are present."""
    print_section("Configuration Validation")
    
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
        print_error("Missing or default required settings in your .env file:")
        for setting in missing_settings:
            print(f"   {RED}•{NC} {setting}")
        print(f"   {WHITE}Please check your .env file and ensure all required values are set.{NC}")
        return False
    
    print_success("All required settings are configured")
    return True

def print_config_summary():
    """Print a summary of the current configuration."""
    print_section("Configuration Summary")
    
    print(f"{WHITE}╔══════════════════════════════════════════════════════════════╗")
    print(f"║                    {BOLD}Configuration Summary{NC}{WHITE}                    ║")
    print(f"╠══════════════════════════════════════════════════════════════════╣")
    
    # Truncate database URL for display
    db_url = settings.DATABASE_URL
    if len(db_url) > 45:
        db_url = db_url[:42] + "..."
    print(f"║ {CYAN}Database:{NC} {db_url:<45} ║")
    
    # Format admin user info
    admin_info = f"{settings.ADMIN_USERNAME} ({settings.ADMIN_EMAIL})"
    if len(admin_info) > 45:
        admin_info = admin_info[:42] + "..."
    print(f"║ {CYAN}Admin User:{NC} {admin_info:<45} ║")
    
    # Format service token
    token_display = f"{settings.SERVICE_TOKEN[:10]}..."
    print(f"║ {CYAN}Service Token:{NC} {token_display:<45} ║")
    
    print(f"╚══════════════════════════════════════════════════════════════════╝")

async def reset_db():
    """Completely reset the PostgreSQL database schema."""
    print_section("Database Reset")
    
    try:
        async with engine.begin() as conn:
            print_progress("Dropping entire 'public' schema with CASCADE")
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            print_success("Public schema dropped successfully")
            
            print_progress("Recreating 'public' schema")
            await conn.execute(text("CREATE SCHEMA public"))
            print_success("Public schema recreated successfully")
            
            print_progress("Creating all database tables from unified models")
            await conn.run_sync(Base.metadata.create_all)
            print_success("All database tables created successfully")
            
        print_success("Database schema reset complete")
    except Exception as e:
        print_error(f"Database reset failed: {e}")
        print(f"   {WHITE}This may indicate a connection issue or insufficient database privileges.{NC}")
        print(f"   {WHITE}Ensure PostgreSQL is running and the database user has CREATE/DROP privileges.{NC}")
        raise

async def create_admin_user():
    """Create default admin user using settings from .env file."""
    print_section("Admin User Creation")
    
    try:
        async with async_session() as session:
            existing_admin = await get_user_by_username(session, settings.ADMIN_USERNAME)
            if existing_admin:
                print_warning(f"Admin user '{settings.ADMIN_USERNAME}' already exists")
                return
            
            print_progress(f"Creating admin user '{settings.ADMIN_USERNAME}'")
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
            print_success(f"Admin user '{settings.ADMIN_USERNAME}' created successfully")
    except Exception as e:
        print_error(f"Admin user creation failed: {e}")
        raise

async def create_predefined_behaviors():
    """Create a set of default lighting behaviors if they don't already exist."""
    print_section("Predefined Lighting Behaviors")

    predefined_behaviors = [
        {
            "name": "Fixed 50%",
            "behavior_type": LightingBehaviorType.FIXED,
            "enabled": True,
            "behavior_config": {"intensity": 0.5}
        },
        {
            "name": "Standard Diurnal",
            "behavior_type": LightingBehaviorType.DIURNAL,
            "enabled": True,
            "behavior_config": {
              "timing": {
                "sunrise_start": "08:00", "sunrise_end": "10:00",
                "peak_start": "10:00", "peak_end": "18:00",
                "sunset_start": "18:00", "sunset_end": "20:00"
              },
              "channels": [],
              "ramp_curve": "exponential"
            }
        },
        {
            "name": "Simple Moonlight",
            "behavior_type": LightingBehaviorType.MOONLIGHT,
            "enabled": True,
            "behavior_config": {"intensity": 0.05, "start_time": "20:00", "end_time": "08:00"}
        },
        {
            "name": "Scheduled Lunar",
            "behavior_type": LightingBehaviorType.LUNAR,
            "enabled": True,
            "behavior_config": {
              "mode": "scheduled",
              "max_intensity": 0.1,
              "start_time": "21:00",
              "end_time": "06:00"
            }
        }
    ]

    async with async_session() as session:
        for behavior_data in predefined_behaviors:
            existing = await lighting_behavior.get_by_name(session, name=behavior_data["name"])
            if existing:
                print_warning(f"Behavior '{behavior_data['name']}' already exists. Skipping.")
                continue

            print_progress(f"Creating behavior: '{behavior_data['name']}'")
            behavior_create = LightingBehaviorCreate(**behavior_data)
            await lighting_behavior.create(session, obj_in=behavior_create)
            print_success(f"Successfully created '{behavior_data['name']}' behavior.")

async def main():
    """Main function to initialize database and create admin user."""
    parser = argparse.ArgumentParser(description="Initialize Bella's Reef database")
    parser.add_argument("--check", action="store_true", help="Validate configuration only")
    parser.add_argument("--dry-run", action="store_true", help="Check config and print summary")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output with detailed progress")
    parser.add_argument("--silent", "-s", action="store_true", help="Suppress all output except errors")
    
    args = parser.parse_args()
    
    # Suppress output if silent mode
    if args.silent:
        # Redirect stdout to devnull for silent mode
        import os
        sys.stdout = open(os.devnull, 'w')
    
    print_banner()
    
    if not check_env_file():
        sys.exit(1)
    
    if not validate_required_settings():
        sys.exit(1)
    
    print_config_summary()
    
    if args.check or args.dry_run:
        print_success("Dry run complete. No database changes made")
        return
    
    print_section("Destructive Operation Warning")
    
    print_warning("DESTRUCTIVE OPERATION WARNING!")
    print(f"   {RED}This will COMPLETELY RESET the database at:{NC}")
    print(f"   {CYAN}→ {settings.DATABASE_URL}{NC}")
    print(f"   {RED}All existing data in the 'public' schema will be PERMANENTLY LOST!{NC}")
    
    print(f"\n{YELLOW}💡 Tip:{NC} Consider backing up your database before proceeding:")
    print(f"   {CYAN}pg_dump -h localhost -U your_user your_db > backup_$(date +%Y%m%d_%H%M%S).sql{NC}")
    
    print(f"\n{YELLOW}   Are you absolutely sure you want to continue?{NC}")
    print(f"   {WHITE}Type '{BOLD}YES{NC}' to confirm: {NC}", end="")
    
    response = input().strip()
    if response != "YES":
        print_error("Database initialization cancelled")
        sys.exit(0)
    
    try:
        await reset_db()
        await create_admin_user()
        await create_predefined_behaviors()
        
        print_section("Success")
        print(f"{GREEN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║                    {BOLD}🎉 SUCCESS! 🎉{NC}{GREEN}                    ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{NC}")
        print(f"\n{GREEN}✓{NC} Database initialized successfully!")
        print(f"{GREEN}✓{NC} Admin user '{settings.ADMIN_USERNAME}' created!")
        print(f"\n{BLUE}Next Steps:{NC}")
        print(f"   1. Start the core service: {CYAN}./scripts/start_api_core.sh{NC}")
        print(f"   2. Start other services: {CYAN}./scripts/start_all.sh{NC}")
        
    except Exception as e:
        print(f"\n{RED}╔══════════════════════════════════════════════════════════════╗")
        print(f"║                    {BOLD}❌ ERROR ❌{NC}{RED}                    ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{NC}")
        print(f"\n{RED}✗{NC} {BOLD}Database initialization failed:{NC}")
        print(f"   {WHITE}Error:{NC} {e}")
        print(f"\n{YELLOW}💡 Troubleshooting:{NC}")
        print(f"   • Check PostgreSQL is running")
        print(f"   • Verify database credentials in .env")
        print(f"   • Ensure database user has CREATE/DROP privileges")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
