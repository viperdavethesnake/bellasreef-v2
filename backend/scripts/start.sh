#!/bin/bash
set -e

VENV_PATH="$HOME/.venvs/bellasreef"

echo "🚀 Starting FastAPI server..."
source "$VENV_PATH/bin/activate"
uvicorn app.main:app --host 0.0.0.0 --port 8000
