#!/bin/bash

# Bella's Reef Migration Artifact Audit Script
# This script searches for any Alembic or migration-related artifacts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 Bella's Reef Migration Artifact Audit${NC}"
echo "=========================================="

# Search for Alembic files and folders
echo -e "\n${YELLOW}Searching for Alembic files and folders...${NC}"
alembic_files=$(find . -name "*alembic*" -o -name "alembic.ini" -o -name "migrations" -type d 2>/dev/null | grep -v __pycache__ | grep -v .git)

if [ -z "$alembic_files" ]; then
    echo -e "${GREEN}✅ No Alembic files or folders found${NC}"
else
    echo -e "${RED}❌ Found Alembic artifacts:${NC}"
    echo "$alembic_files"
fi

# Search for migration-related imports
echo -e "\n${YELLOW}Searching for migration-related imports...${NC}"
migration_imports=$(grep -r "from alembic\|import alembic\|alembic upgrade\|alembic downgrade" . --include="*.py" --include="*.sh" 2>/dev/null | grep -v __pycache__ | grep -v .git || true)

if [ -z "$migration_imports" ]; then
    echo -e "${GREEN}✅ No migration-related imports found${NC}"
else
    echo -e "${RED}❌ Found migration-related imports:${NC}"
    echo "$migration_imports"
fi

# Search for migration-related text
echo -e "\n${YELLOW}Searching for migration-related text...${NC}"
migration_text=$(grep -r "migration\|Migration" . --include="*.py" --include="*.md" --include="*.txt" 2>/dev/null | grep -v __pycache__ | grep -v .git | grep -v "No migration" | grep -v "migration script" || true)

if [ -z "$migration_text" ]; then
    echo -e "${GREEN}✅ No unexpected migration references found${NC}"
else
    echo -e "${YELLOW}⚠️  Found migration references (may be legitimate):${NC}"
    echo "$migration_text"
fi

# Check for database initialization files
echo -e "\n${YELLOW}Checking database initialization files...${NC}"
if [ -f "scripts/init_db.py" ]; then
    echo -e "${GREEN}✅ scripts/init_db.py found${NC}"
else
    echo -e "${RED}❌ scripts/init_db.py not found${NC}"
fi

# Check for create_all usage
echo -e "\n${YELLOW}Checking for create_all usage...${NC}"
create_all_usage=$(grep -r "create_all" . --include="*.py" 2>/dev/null | grep -v __pycache__ | grep -v .git || true)

if [ -n "$create_all_usage" ]; then
    echo -e "${YELLOW}⚠️  Found create_all usage:${NC}"
    echo "$create_all_usage"
fi

echo -e "\n${GREEN}🎉 Migration audit complete!${NC}" 