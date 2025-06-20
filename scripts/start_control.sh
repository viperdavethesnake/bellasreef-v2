#!/bin/bash
# Bella's Reef - Control Service Robust Start Script
# Handles hardware control - PWM, GPIO, relays

set -e

# Get the project root directory (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONTROL_DIR="$PROJECT_ROOT/control"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[Bella's Reef] Starting Control Service...${NC}"

# Check if virtual environment exists
if [ ! -d "$CONTROL_DIR/venv" ]; then
    echo -e "${RED}No venv found. Run setup first!${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source "$CONTROL_DIR/venv/bin/activate"

# Check if .env file exists
if [ ! -f "$CONTROL_DIR/.env" ]; then
    echo -e "${RED}No .env file found in $CONTROL_DIR. Run setup and configure your environment!${NC}"
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
    echo -e "${RED}Database not initialized! Run: python3 $SCRIPT_DIR/init_db.py${NC}"
    exit 1
elif [ $rc -eq 3 ]; then
    echo -e "${RED}Database connection failed. Check your DB settings in .env.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database ready. Launching service...${NC}"

# Start the service
echo -e "${GREEN}Starting Control Service on port 8003...${NC}"
cd "$CONTROL_DIR"
python3 main.py 