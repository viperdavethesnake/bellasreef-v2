#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  ⚡ LIGHTING API Service ⚡                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo ""
echo "▶ Environment Validation"
set -a
source ./env.example
set +a
echo "⏳ Loading environment variables ✓"
echo ""

if [ "$LIGHTING_API_ENABLED" != "true" ]; then
  echo "❌ Lighting API service is DISABLED (LIGHTING_API_ENABLED != true)"
  exit 0
fi
echo ""
echo "▶ Service Status Check"
echo "✅ Lighting service is enabled"
echo ""

echo "▶ Virtual Environment Setup"
if [ -d "bellasreef-venv" ]; then
  source ./bellasreef-venv/bin/activate
  echo "⏳ Activating virtual environment ✓"
else
  echo "❌ Virtual environment not found: ./bellasreef-venv"
  exit 1
fi
echo ""

echo "▶ Service Configuration"
echo "  • Host: $LIGHTING_API_HOST"
echo "  • Port: $LIGHTING_API_PORT"
echo "  • Debug: $LIGHTING_API_DEBUG"
echo "  • Log Level: $LIGHTING_API_LOG_LEVEL"
echo ""

echo "▶ Starting Service"
echo "✅ Launching Lighting API Service..."
echo "🚀 Lighting API Service is starting on http://$LIGHTING_API_HOST:$LIGHTING_API_PORT"
echo "📖 API Documentation: http://$LIGHTING_API_HOST:$LIGHTING_API_PORT/docs"
echo "🏥 Health Check: http://$LIGHTING_API_HOST:$LIGHTING_API_PORT/health"
echo ""

exec uvicorn lighting.main:app \
  --host "$LIGHTING_API_HOST" \
  --port "$LIGHTING_API_PORT" \
  --log-level "$LIGHTING_API_LOG_LEVEL" \
  $( [ "$LIGHTING_API_DEBUG" == "true" ] && echo "--reload" )
 -a
