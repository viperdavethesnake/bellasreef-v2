#!/bin/bash
# Bella's Reef - Application Startup Script
#
# FEATURES:
# - Robust CLI flags for different startup modes
# - Environment and configuration validation
# - Interactive confirmation for production mode
# - Clear user feedback with status icons
# - Flexible path handling (runs from project root or scripts directory)
# - Comprehensive error handling and exit codes
# - Helpful guidance and next steps
#
# USAGE:
#     ./scripts/start.sh              # Normal startup with validation
#     ./scripts/start.sh --check      # Validate environment only
#     ./scripts/start.sh --prod       # Production mode (no reload)
#     ./scripts/start.sh --debug      # Debug mode with extra logging
#     ./scripts/start.sh --help       # Show help

set -e

# =============================================================================
# Configuration
# =============================================================================
PROJECT_NAME="bellasreef"
VENV_PATH="$HOME/.venvs/$PROJECT_NAME"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Default settings
HOST="0.0.0.0"
PORT="8000"
RELOAD=true
LOG_LEVEL="info"

# =============================================================================
# CLI Argument Parsing
# =============================================================================
CHECK_ONLY=false
PRODUCTION=false
DEBUG=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --prod|--production)
            PRODUCTION=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "   Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$HELP" = true ]; then
    echo "🚀 Bella's Reef Application Startup"
    echo "==================================="
    echo ""
    echo "IMPORTANT: Run this script from the PROJECT ROOT directory"
    echo "   Project root: /path/to/bellasreef-v2/"
    echo "   Script location: backend/scripts/start.sh"
    echo ""
    echo "USAGE:"
    echo "  ./backend/scripts/start.sh         # Normal startup with validation"
    echo "  ./backend/scripts/start.sh --check # Validate environment only"
    echo "  ./backend/scripts/start.sh --prod  # Production mode (no reload)"
    echo "  ./backend/scripts/start.sh --debug # Debug mode with extra logging"
    echo "  ./backend/scripts/start.sh --help  # Show this help"
    echo ""
    echo "FEATURES:"
    echo "  ✅ Environment validation"
    echo "  ✅ Configuration checking"
    echo "  ✅ Development and production modes"
    echo "  ✅ Automatic reload in development"
    echo "  ✅ Health check and status monitoring"
    echo "  ✅ Proper module path resolution"
    echo ""
    exit 0
fi

# =============================================================================
# Helper Functions
# =============================================================================
print_status() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

print_info() {
    echo "ℹ️  $1"
}

check_environment() {
    print_info "Checking environment..."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found: $VENV_PATH"
        print_info "Run setup first: ./scripts/setup.sh"
        return 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning ".env file not found: $ENV_FILE"
        print_info "Run setup first: ./scripts/setup.sh"
        return 1
    fi
    
    print_status "Environment check passed"
    return 0
}

validate_configuration() {
    print_info "Validating configuration..."
    
    # Activate venv for Python validation
    source "$VENV_PATH/bin/activate"
    
    # Run config validation
    if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from app.core.config import settings
    print('✅ Configuration loaded successfully')
    print(f'   Environment: {settings.ENV}')
    print(f'   Debug Mode: {settings.DEBUG}')
    print(f'   Database: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}')
    print(f'   CORS Origins: {settings.CORS_ORIGINS}')
    print(f'   Hardware Platform: {settings.RPI_PLATFORM}')
    
    # Security warnings
    if settings.ENV == 'production' and settings.DEBUG:
        print('⚠️  WARNING: DEBUG=True in production environment')
    if '*' in settings.CORS_ORIGINS:
        print('⚠️  WARNING: Wildcard CORS enabled')
    if settings.ADMIN_PASSWORD == 'reefrocks':
        print('⚠️  WARNING: Using default admin password')
        
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    sys.exit(1)
"; then
        print_status "Configuration validation passed"
        return 0
    else
        print_error "Configuration validation failed"
        return 1
    fi
}

check_database_connection() {
    print_info "Checking database connection..."
    
    # Activate venv for Python validation
    source "$VENV_PATH/bin/activate"
    
    # Run database connection test
    if python3 -c "
import sys
import asyncio
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from app.db.base import engine
    from app.core.config import settings
    
    async def test_connection():
        try:
            async with engine.begin() as conn:
                await conn.execute('SELECT 1')
            print('✅ Database connection successful')
            return True
        except Exception as e:
            print(f'❌ Database connection failed: {e}')
            return False
    
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
    
except Exception as e:
    print(f'❌ Database test failed: {e}')
    sys.exit(1)
"; then
        print_status "Database connection test passed"
        return 0
    else
        print_warning "Database connection test failed"
        print_info "Make sure PostgreSQL is running and configured correctly"
        return 1
    fi
}

setup_startup_mode() {
    if [ "$PRODUCTION" = true ]; then
        print_info "Setting up production mode..."
        RELOAD=false
        LOG_LEVEL="warning"
        
        # Confirm production startup
        if [ "$CHECK_ONLY" = false ]; then
            echo ""
            print_warning "Starting in PRODUCTION mode"
            echo "   - No auto-reload"
            echo "   - Reduced logging"
            echo "   - Optimized for performance"
            echo ""
            read -p "Continue with production startup? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Production startup cancelled"
                exit 0
            fi
        fi
    elif [ "$DEBUG" = true ]; then
        print_info "Setting up debug mode..."
        RELOAD=true
        LOG_LEVEL="debug"
    else
        print_info "Setting up development mode..."
        RELOAD=true
        LOG_LEVEL="info"
    fi
}

start_application() {
    print_info "Starting Bella's Reef application..."
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Check if app module exists
    if [ ! -f "$PROJECT_ROOT/app/main.py" ]; then
        print_error "FastAPI app module not found: $PROJECT_ROOT/app/main.py"
        print_error "Expected structure: backend/app/main.py"
        print_info "Make sure you're running from the project root directory"
        exit 1
    fi
    
    # Change to backend directory for proper module resolution
    cd "$PROJECT_ROOT"
    
    # Build uvicorn command with proper module path
    UVICORN_CMD="uvicorn app.main:app --host $HOST --port $PORT --log-level $LOG_LEVEL"
    
    if [ "$RELOAD" = true ]; then
        UVICORN_CMD="$UVICORN_CMD --reload"
    fi
    
    echo ""
    echo "🚀 Starting FastAPI server..."
    echo "   Working Directory: $(pwd)"
    echo "   App Module: app.main:app"
    echo "   Host: $HOST"
    echo "   Port: $PORT"
    echo "   Log Level: $LOG_LEVEL"
    echo "   Reload: $RELOAD"
    echo "   Environment: $(source $VENV_PATH/bin/activate && python3 -c 'import sys; sys.path.insert(0, "'$PROJECT_ROOT'"); from app.core.config import settings; print(settings.ENV)')"
    echo ""
    
    # Start the application
    if eval "$UVICORN_CMD"; then
        print_status "Application started successfully"
    else
        print_error "Failed to start application"
        print_info "Check that you're running from the project root directory"
        print_info "Expected command: ./backend/scripts/start.sh"
        exit 1
    fi
}

# =============================================================================
# Main Startup Process
# =============================================================================
main() {
    echo "🚀 Bella's Reef Application Startup"
    echo "==================================="
    echo ""
    
    # Check if we're in the right directory structure
    if [ ! -d "$PROJECT_ROOT/app" ]; then
        print_error "Cannot find 'app' directory: $PROJECT_ROOT/app"
        print_error "Expected structure: backend/app/"
        print_info "Make sure you're running from the PROJECT ROOT directory"
        print_info "Current directory: $(pwd)"
        print_info "Expected command: ./backend/scripts/start.sh"
        exit 1
    fi
    
    # Environment validation
    if ! check_environment; then
        print_error "Environment validation failed"
        exit 1
    fi
    
    # Configuration validation
    if ! validate_configuration; then
        print_error "Configuration validation failed"
        exit 1
    fi
    
    # Check-only mode
    if [ "$CHECK_ONLY" = true ]; then
        print_info "Check-only mode - validating environment..."
        
        if check_database_connection; then
            print_status "Environment validation complete"
            echo ""
            echo "📋 Environment Status:"
            echo "   ✅ Virtual environment: $VENV_PATH"
            echo "   ✅ Configuration: Valid"
            echo "   ✅ Database: Connected"
            echo ""
            echo "🔧 Ready to start with: ./scripts/start.sh"
            exit 0
        else
            print_error "Environment validation failed"
            exit 1
        fi
    fi
    
    # Database connection check (non-blocking warning)
    check_database_connection || true
    
    # Setup startup mode
    setup_startup_mode
    
    # Success message
    echo ""
    echo "🎉 Bella's Reef application starting!"
    echo ""
    echo "📋 Access Information:"
    echo "   🌐 API: http://localhost:$PORT"
    echo "   📚 Documentation: http://localhost:$PORT/docs"
    echo "   🔧 Interactive API: http://localhost:$PORT/redoc"
    echo "   🏥 Health Check: http://localhost:$PORT/health"
    echo ""
    echo "🔧 Development Tips:"
    echo "   - Press Ctrl+C to stop the server"
    echo "   - Auto-reload is enabled in development"
    echo "   - Check logs for any errors"
    echo "   - Use --prod flag for production mode"
    echo ""
    
    # Start the application
    start_application
}

# Run main function
main "$@"
