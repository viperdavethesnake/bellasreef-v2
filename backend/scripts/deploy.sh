#!/bin/bash
# Bella's Reef - Deployment Script
#
# FEATURES:
# - Robust CLI flags for different deployment modes
# - Environment and configuration validation
# - Interactive confirmation for production deployment
# - Clear user feedback with status icons
# - Flexible path handling (runs from project root or scripts directory)
# - Comprehensive error handling and exit codes
# - Helpful guidance and next steps
#
# USAGE:
#     ./scripts/deploy.sh              # Normal deployment with validation
#     ./scripts/deploy.sh --check      # Validate environment only
#     ./scripts/deploy.sh --prod       # Production deployment
#     ./scripts/deploy.sh --force      # Skip confirmations
#     ./scripts/deploy.sh --help       # Show help

set -e

# =============================================================================
# Configuration
# =============================================================================
PROJECT_NAME="bellasreef"
VENV_PATH="$HOME/.venvs/$PROJECT_NAME"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# =============================================================================
# CLI Argument Parsing
# =============================================================================
CHECK_ONLY=false
PRODUCTION=false
FORCE=false
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
        --force)
            FORCE=true
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
    echo "🚀 Bella's Reef Deployment"
    echo "=========================="
    echo ""
    echo "USAGE:"
    echo "  ./scripts/deploy.sh              # Normal deployment with validation"
    echo "  ./scripts/deploy.sh --check      # Validate environment only"
    echo "  ./scripts/deploy.sh --prod       # Production deployment"
    echo "  ./scripts/deploy.sh --force      # Skip confirmations"
    echo "  ./scripts/deploy.sh --help       # Show this help"
    echo ""
    echo "FEATURES:"
    echo "  ✅ Environment setup and validation"
    echo "  ✅ Database initialization"
    echo "  ✅ Application startup"
    echo "  ✅ Production mode support"
    echo "  ✅ Health checks and monitoring"
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

check_prerequisites() {
    print_info "Checking deployment prerequisites..."
    
    # Check if scripts exist
    if [ ! -f "$PROJECT_ROOT/scripts/setup.sh" ]; then
        print_error "setup.sh not found: $PROJECT_ROOT/scripts/setup.sh"
        return 1
    fi
    
    if [ ! -f "$PROJECT_ROOT/scripts/init_db.py" ]; then
        print_error "init_db.py not found: $PROJECT_ROOT/scripts/init_db.py"
        return 1
    fi
    
    if [ ! -f "$PROJECT_ROOT/scripts/start.sh" ]; then
        print_error "start.sh not found: $PROJECT_ROOT/scripts/start.sh"
        return 1
    fi
    
    # Check if .env exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning ".env file not found: $ENV_FILE"
        if [ -f "$PROJECT_ROOT/env.example" ]; then
            print_info "Copying env.example to .env..."
            cp "$PROJECT_ROOT/env.example" "$ENV_FILE"
            print_warning "Please edit .env with your configuration before continuing"
            if [ "$FORCE" = false ]; then
                read -p "Continue with deployment? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    print_error "Deployment cancelled"
                    exit 1
                fi
            fi
        else
            print_error "env.example not found. Please create .env file manually"
            return 1
        fi
    fi
    
    print_status "Prerequisites check passed"
    return 0
}

validate_environment() {
    print_info "Validating environment..."
    
    # Run setup check
    if ! "$PROJECT_ROOT/scripts/setup.sh" --check; then
        print_error "Environment validation failed"
        return 1
    fi
    
    print_status "Environment validation passed"
    return 0
}

run_setup() {
    print_info "Running environment setup..."
    
    if [ "$FORCE" = true ]; then
        if ! "$PROJECT_ROOT/scripts/setup.sh" --force; then
            print_error "Environment setup failed"
            return 1
        fi
    else
        if ! "$PROJECT_ROOT/scripts/setup.sh"; then
            print_error "Environment setup failed"
            return 1
        fi
    fi
    
    print_status "Environment setup completed"
    return 0
}

initialize_database() {
    print_info "Initializing database..."
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Run database initialization
    if [ "$FORCE" = true ]; then
        if ! python3 "$PROJECT_ROOT/scripts/init_db.py"; then
            print_error "Database initialization failed"
            return 1
        fi
    else
        if ! python3 "$PROJECT_ROOT/scripts/init_db.py"; then
            print_error "Database initialization failed"
            return 1
        fi
    fi
    
    print_status "Database initialization completed"
    return 0
}

start_application() {
    print_info "Starting application..."
    
    if [ "$PRODUCTION" = true ]; then
        print_info "Starting in production mode..."
        if ! "$PROJECT_ROOT/scripts/start.sh" --prod; then
            print_error "Application startup failed"
            return 1
        fi
    else
        print_info "Starting in development mode..."
        if ! "$PROJECT_ROOT/scripts/start.sh"; then
            print_error "Application startup failed"
            return 1
        fi
    fi
    
    print_status "Application started successfully"
    return 0
}

check_health() {
    print_info "Checking application health..."
    
    # Wait a moment for the application to start
    sleep 3
    
    # Check if the application is responding
    if curl -f -s "http://localhost:8000/" > /dev/null; then
        print_status "Application health check passed"
        return 0
    else
        print_warning "Application health check failed"
        print_info "The application may still be starting up"
        return 1
    fi
}

# =============================================================================
# Main Deployment Process
# =============================================================================
main() {
    echo "🚀 Bella's Reef Deployment"
    echo "=========================="
    echo ""
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites check failed"
        exit 1
    fi
    
    # Check-only mode
    if [ "$CHECK_ONLY" = true ]; then
        print_info "Check-only mode - validating environment..."
        if validate_environment; then
            print_status "Environment validation complete"
            echo ""
            echo "📋 Environment Status:"
            echo "   ✅ Prerequisites: Met"
            echo "   ✅ Configuration: Valid"
            echo "   ✅ Dependencies: Installed"
            echo ""
            echo "🔧 Ready to deploy with: ./scripts/deploy.sh"
            exit 0
        else
            print_error "Environment validation failed"
            exit 1
        fi
    fi
    
    # Production deployment confirmation
    if [ "$PRODUCTION" = true ] && [ "$FORCE" = false ]; then
        echo ""
        print_warning "PRODUCTION DEPLOYMENT"
        echo "   - Environment: Production"
        echo "   - Database: Will be initialized"
        echo "   - Application: Production mode"
        echo "   - Auto-reload: Disabled"
        echo ""
        read -p "Continue with production deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Production deployment cancelled"
            exit 0
        fi
    fi
    
    # Run deployment steps
    print_info "Starting deployment process..."
    
    # Step 1: Environment setup
    if ! run_setup; then
        print_error "Deployment failed at environment setup"
        exit 1
    fi
    
    # Step 2: Database initialization
    if ! initialize_database; then
        print_error "Deployment failed at database initialization"
        exit 1
    fi
    
    # Step 3: Application startup
    if ! start_application; then
        print_error "Deployment failed at application startup"
        exit 1
    fi
    
    # Step 4: Health check
    check_health || true
    
    # Success message
    echo ""
    echo "🎉 Bella's Reef deployment complete!"
    echo ""
    echo "📋 Deployment Summary:"
    echo "   ✅ Environment: Setup complete"
    echo "   ✅ Database: Initialized"
    echo "   ✅ Application: Started"
    echo "   ✅ Health: Checked"
    echo ""
    echo "🌐 Access Information:"
    echo "   API: http://localhost:8000"
    echo "   Documentation: http://localhost:8000/docs"
    echo "   Interactive API: http://localhost:8000/redoc"
    echo "   Health Check: http://localhost:8000/health"
    echo ""
    echo "🔧 Management Commands:"
    echo "   Stop: Ctrl+C (if running in foreground)"
    echo "   Restart: ./scripts/start.sh"
    echo "   Check Status: ./scripts/start.sh --check"
    echo "   View Logs: Check terminal output"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Test the API endpoints"
    echo "   2. Configure monitoring and logging"
    echo "   3. Set up backup procedures"
    echo "   4. Document your deployment"
    echo ""
}

# Run main function
main "$@"
