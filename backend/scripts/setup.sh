#!/bin/bash
set -e

PROJECT_NAME=bellasreef
VENV_PATH="$HOME/.venvs/$PROJECT_NAME"

echo "🔧 Setting up virtual environment at $VENV_PATH..."
if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"

echo "⬆️  Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "📂 Running Alembic migrations..."
alembic upgrade head

echo "✅ Setup complete!"
