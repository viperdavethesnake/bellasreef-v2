#!/bin/bash
# Bella's Reef - Core Service Startup Script
# Handles user authentication, session management, and system health

set -e

# Get the project root directory (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CORE_DIR="$PROJECT_ROOT/core"
SHARED_DIR="$PROJECT_ROOT/shared"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Bella's Reef Core Service...${NC}"

# Change to core directory
cd "$CORE_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r "$SHARED_DIR/requirements.txt"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Copying from example...${NC}"
    cp env.example .env
    echo -e "${RED}Please edit .env file with your configuration before starting the service.${NC}"
    exit 1
fi

# Check if database is initialized
echo -e "${YELLOW}Checking database initialization...${NC}"
if ! python -c "
import sys
sys.path.insert(0, '$SHARED_DIR')
from shared.db.database import engine
from sqlalchemy import text
import asyncio

async def check_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
            result = await conn.execute(text(\"\"\"
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            \"\"\"))
            if not result.scalar():
                print('Database tables not found')
                sys.exit(1)
    except Exception as e:
        print(f'Database connection failed: {e}')
        sys.exit(1)

asyncio.run(check_db())
" 2>/dev/null; then
    echo -e "${RED}❌ Database not initialized!${NC}"
    echo -e "${YELLOW}Please run: python $SCRIPT_DIR/init_db.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database connectivity verified${NC}"

# Start the service
echo -e "${GREEN}Starting Core Service on port 8000...${NC}"
python main.py 