#!/usr/bin/env python3
"""
Database migration script for device unit support.

This script adds the new unit, min_value, and max_value fields to the devices table
and updates existing device records with appropriate default values.

USAGE:
    python scripts/migrate_device_units.py
"""

import sys
from pathlib import Path

# --- Ensure backend is on the Python path ---
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.database import engine
from app.core.config import settings

async def migrate_device_units():
    """Add unit support fields to devices table"""
    
    print("🔧 Device Unit Migration")
    print("=" * 50)
    
    try:
        async with engine.begin() as conn:
            # Check if unit column already exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'devices' AND column_name = 'unit'
            """))
            
            if result.fetchone():
                print("✅ Unit column already exists")
            else:
                print("📝 Adding unit column to devices table...")
                await conn.execute(text("""
                    ALTER TABLE devices 
                    ADD COLUMN unit VARCHAR(20)
                """))
                print("✅ Unit column added")
            
            # Check if min_value column already exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'devices' AND column_name = 'min_value'
            """))
            
            if result.fetchone():
                print("✅ min_value column already exists")
            else:
                print("📝 Adding min_value column to devices table...")
                await conn.execute(text("""
                    ALTER TABLE devices 
                    ADD COLUMN min_value FLOAT
                """))
                print("✅ min_value column added")
            
            # Check if max_value column already exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'devices' AND column_name = 'max_value'
            """))
            
            if result.fetchone():
                print("✅ max_value column already exists")
            else:
                print("📝 Adding max_value column to devices table...")
                await conn.execute(text("""
                    ALTER TABLE devices 
                    ADD COLUMN max_value FLOAT
                """))
                print("✅ max_value column added")
            
            # Create index on unit column if it doesn't exist
            result = await conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'devices' AND indexname = 'ix_devices_unit'
            """))
            
            if result.fetchone():
                print("✅ Unit index already exists")
            else:
                print("📝 Creating index on unit column...")
                await conn.execute(text("""
                    CREATE INDEX ix_devices_unit ON devices(unit)
                """))
                print("✅ Unit index created")
            
            # Update existing devices with default units based on device type
            print("📝 Updating existing devices with default units...")
            
            # Temperature sensors
            await conn.execute(text("""
                UPDATE devices 
                SET unit = 'C' 
                WHERE device_type = 'temperature_sensor' AND unit IS NULL
            """))
            
            # Outlets
            await conn.execute(text("""
                UPDATE devices 
                SET unit = 'state' 
                WHERE device_type = 'outlet' AND unit IS NULL
            """))
            
            # Count updated devices
            result = await conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM devices 
                WHERE unit IS NOT NULL
            """))
            updated_count = result.fetchone()[0]
            
            print(f"✅ Updated {updated_count} devices with default units")
            
            # Show summary of device types and units
            print("\n📊 Device Summary:")
            result = await conn.execute(text("""
                SELECT device_type, unit, COUNT(*) as count
                FROM devices 
                WHERE unit IS NOT NULL
                GROUP BY device_type, unit
                ORDER BY device_type, unit
            """))
            
            for row in result.fetchall():
                device_type, unit, count = row
                print(f"   {device_type}: {unit} ({count} devices)")
            
            print("\n✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_device_units()) 