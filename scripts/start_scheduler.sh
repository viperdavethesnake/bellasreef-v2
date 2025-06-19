#!/bin/bash
# Bella's Reef - Scheduler Service Robust Start Script
# Handles job scheduling and automation management

set -e

# Get the project root directory (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEDULER_DIR="$PROJECT_ROOT/scheduler"
SHARED_DIR="$PROJECT_ROOT/shared"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[Bella's Reef] Starting Scheduler Service...${NC}"

# Check if virtual environment exists
if [ ! -d "$SCHEDULER_DIR/venv" ]; then
    echo -e "${RED}No venv found. Run setup first!${NC}"; exit 1
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source "$SCHEDULER_DIR/venv/bin/activate"

# Check if .env file exists
if [ ! -f "$SCHEDULER_DIR/.env" ]; then
    echo -e "${RED}No .env file found in $SCHEDULER_DIR. Run setup and configure your environment!${NC}"; exit 1
fi

# Minimal DB check
python3 - <<EOF
import sys
sys.path.insert(0, '$SHARED_DIR')
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
                sys.exit(2)
    except Exception as e:
        print(f'Database connection failed: {e}')
        sys.exit(3)
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
echo -e "${GREEN}Starting Scheduler Service on port 8001...${NC}"
cd "$SCHEDULER_DIR"
python3 main.py 