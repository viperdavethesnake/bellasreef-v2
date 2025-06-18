#!/bin/bash
set -e

# Determine the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$HOME/.venvs/bellasreef"

echo "🔧 Checking Python 3 and required packages..."
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is not installed."
  exit 1
fi

cd "$PROJECT_ROOT"

if [ ! -d "$VENV_PATH" ]; then
  echo "🧪 Creating virtual environment at $VENV_PATH..."
  python3 -m venv "$VENV_PATH"
fi

echo "🌀 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

echo "⬆️  Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "✅ Setup complete."
