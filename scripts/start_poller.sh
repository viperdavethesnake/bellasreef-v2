#!/bin/bash
# Bella's Reef - Poller Service Robust Start Script
# Handles device polling, sensor data collection, and alert management

set -e

# Get script and project directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
POLLER_DIR="$PROJECT_ROOT/poller"
CORE_DIR="$PROJECT_ROOT/core"
VENV_DIR="$POLLER_DIR/bellasreef-poller-venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[Bella's Reef] Starting Poller Service...${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}No virtual environment found. Run setup first!${NC}"
    echo -e "${YELLOW}Expected: $VENV_DIR${NC}"
    exit 1
fi

# Check if the correct virtual environment is activated
# This prevents dependency issues and ensures the service runs with the correct Python packages
if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
    echo -e "${RED}❌ Error: Poller Service virtual environment is not activated.${NC}"
    echo -e "   Current VIRTUAL_ENV: ${VIRTUAL_ENV:-'not set'}"
    echo -e "   Expected VIRTUAL_ENV: $VENV_DIR"
    echo ""
    echo -e "   Please activate the virtual environment first:"
    echo -e "   source $VENV_DIR/bin/activate"
    echo ""
    echo -e "   Then run this script again."
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if .env file exists
if [ ! -f "$CORE_DIR/.env" ]; then
    echo -e "${RED}No .env file found in $CORE_DIR. Run setup and configure your environment!${NC}"
    exit 1
fi

# Set PYTHONPATH to include project root for shared module imports
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo -e "${YELLOW}📁 PYTHONPATH set to: $PROJECT_ROOT${NC}"

# Minimal DB check
python3 - <<EOF
from shared.db.database import engine
from sqlalchemy import text
import asyncio

async def check_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """))
            if not result.scalar():
                print('DB tables missing')
                exit(2)
    except Exception as e:
        print(f'Database connection failed: {e}')
        exit(3)

asyncio.run(check_db())
EOF

rc=$?
if [ $rc -eq 2 ]; then
    echo -e "${RED}Database not initialized! Run: python3 $SCRIPT_DIR/init_db.py${NC}"; exit 1
elif [ $rc -eq 3 ]; then
    echo -e "${RED}Database connection failed. Check your DB settings in .env.${NC}"; exit 1
fi
echo -e "${GREEN}✅ Database ready. Launching service...${NC}"

# Start the service
echo -e "${GREEN}Starting Poller Service on port 8002...${NC}"
cd "$POLLER_DIR"
python3 main.py 