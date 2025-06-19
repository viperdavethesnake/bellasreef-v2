#!/bin/bash
# Bella's Reef - Core Service Robust Setup Script
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CORE_DIR="$PROJECT_ROOT/core"
SHARED_DIR="$PROJECT_ROOT/shared"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
echo -e "${GREEN}[Bella's Reef] Setting up Core Service...${NC}"
# Python & venv check
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required. Please install it!${NC}"; exit 1
fi
PYV=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)'; then :; else
    echo -e "${RED}Python 3.11+ is required. Found $PYV.${NC}"; exit 1
fi
if [ ! -d "$CORE_DIR/venv" ]; then
    echo -e "${YELLOW}Creating venv...${NC}"
    python3 -m venv "$CORE_DIR/venv"
fi
source "$CORE_DIR/venv/bin/activate"
# Install dependencies
if [ ! -f "$SHARED_DIR/requirements.txt" ]; then
    echo -e "${RED}Missing requirements.txt in shared!${NC}"; exit 1
fi
pip install --upgrade pip
pip install -r "$SHARED_DIR/requirements.txt"
# .env check and reminder
if [ ! -f "$CORE_DIR/.env" ]; then
    cp "$CORE_DIR/env.example" "$CORE_DIR/.env"
    echo -e "${YELLOW}Created .env from example. Edit this file before starting the service!${NC}"
fi
# Warn if using unsafe defaults
grep -q "changeme" "$CORE_DIR/.env" && \
    echo -e "${YELLOW}WARNING: You are using a default SERVICE_TOKEN! Change it before production.${NC}"
grep -q "your_super_secret_key_here" "$CORE_DIR/.env" && \
    echo -e "${YELLOW}WARNING: You are using a default SECRET_KEY! Change it before production.${NC}"
echo -e "${GREEN}✅ Setup complete. Next:${NC}"
echo -e "   1. Edit $CORE_DIR/.env with your secure settings."
echo -e "   2. Run: python3 $SCRIPT_DIR/init_db.py"
echo -e "   3. Start: $SCRIPT_DIR/start_core.sh" 