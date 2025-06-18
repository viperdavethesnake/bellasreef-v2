#!/bin/bash

set -e

VENV_PATH="$HOME/.venvs/bellasreef"

echo "🔧 Creating virtual environment at $VENV_PATH..."
python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

echo "⬆️  Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "📂 Running Alembic migrations..."
alembic upgrade head

echo "✅ Environment is ready!"
echo ""
echo "To activate it later:"
echo "source $VENV_PATH/bin/activate"
