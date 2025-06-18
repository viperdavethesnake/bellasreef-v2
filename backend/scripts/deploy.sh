#!/bin/bash
set -e

echo "🚀 Running setup..."
./scripts/setup.sh

echo "🛠️ Skipping DB init for now..."
# Uncomment this line later if needed:
# source ~/.venvs/bellasreef/bin/activate && python scripts/init_db.py

echo "🔄 Starting application..."
./scripts/start.sh
