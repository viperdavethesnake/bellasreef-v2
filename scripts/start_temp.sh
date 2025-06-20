#!/bin/bash

# Bella's Reef Temperature Service Start Script
# This script starts the temperature service with proper environment setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the absolute path to the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$PROJECT_ROOT/temp"

print_status "Starting Bella's Reef Temperature Service..."
print_status "Project root: $PROJECT_ROOT"
print_status "Temperature service directory: $TEMP_DIR"

# Check if temperature service directory exists
check_service_directory() {
    if [[ ! -d "$TEMP_DIR" ]]; then
        print_error "Temperature service directory not found: $TEMP_DIR"
        print_error "Please run setup first: ./scripts/setup_temp.sh"
        exit 1
    fi
    print_success "Temperature service directory found"
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -d "$TEMP_DIR/venv" ]]; then
        print_error "Virtual environment not found: $TEMP_DIR/venv"
        print_error "Please run setup first: ./scripts/setup_temp.sh"
        exit 1
    fi
    print_success "Virtual environment found"
}

# Check if environment file exists
check_env_file() {
    if [[ ! -f "$TEMP_DIR/.env" ]]; then
        print_error "Environment file not found: $TEMP_DIR/.env"
        print_error "Please run setup first: ./scripts/setup_temp.sh"
        exit 1
    fi
    print_success "Environment file found"
    
    # Check if service is enabled
    if grep -q "^TEMP_ENABLED=false" "$TEMP_DIR/.env"; then
        print_error "Temperature Service is disabled in $TEMP_DIR/.env"
        print_error "Set TEMP_ENABLED=true to enable the service"
        exit 1
    fi
    
    if grep -q "^TEMP_ENABLED=true" "$TEMP_DIR/.env"; then
        print_success "Temperature Service is enabled"
    else
        print_warning "TEMP_ENABLED not found in .env, defaulting to enabled"
    fi
}

# Check if main.py exists
check_main_file() {
    if [[ ! -f "$TEMP_DIR/main.py" ]]; then
        print_error "Main application file not found: $TEMP_DIR/main.py"
        print_error "Temperature service files may be missing"
        exit 1
    fi
    print_success "Main application file found"
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source "$TEMP_DIR/venv/bin/activate"
    print_success "Virtual environment activated"
}

# Check Python dependencies
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    # Check if key packages are installed
    if ! python -c "import fastapi" 2>/dev/null; then
        print_error "FastAPI not found. Please run setup first: ./scripts/setup_temp.sh"
        exit 1
    fi
    
    if ! python -c "import sqlalchemy" 2>/dev/null; then
        print_error "SQLAlchemy not found. Please run setup first: ./scripts/setup_temp.sh"
        exit 1
    fi
    
    print_success "Python dependencies verified"
}

# Check database connectivity
check_database() {
    print_status "Checking database connectivity..."
    
    # Try to import and test database connection
    cd "$TEMP_DIR"
    if python -c "
import os
import sys
sys.path.insert(0, '..')
from shared.db.database import async_session
from temp.config import settings
print('Database configuration loaded successfully')
" 2>/dev/null; then
        print_success "Database configuration verified"
    else
        print_warning "Database configuration check failed"
        print_warning "Service will attempt to connect at startup"
    fi
}

# Check 1-wire subsystem
check_1wire() {
    print_status "Checking 1-wire subsystem..."
    
    if [[ -d "/sys/bus/w1/devices" ]]; then
        SENSOR_COUNT=$(ls /sys/bus/w1/devices/28-* 2>/dev/null | wc -l)
        if [[ $SENSOR_COUNT -gt 0 ]]; then
            print_success "1-wire subsystem available with $SENSOR_COUNT sensor(s)"
        else
            print_warning "1-wire subsystem available but no sensors found"
        fi
    else
        print_warning "1-wire subsystem not available"
        print_warning "Hardware features will not work"
    fi
}

# Start the service
start_service() {
    print_status "Starting temperature service..."
    
    cd "$TEMP_DIR"
    
    # Set environment variables
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # Start the service
    print_status "Starting FastAPI application..."
    print_status "Service will be available at: http://localhost:8004"
    print_status "API documentation: http://localhost:8004/docs"
    print_status "Press Ctrl+C to stop the service"
    echo
    
    # Run the service
    python main.py
}

# Handle script interruption
cleanup() {
    print_status "Shutting down temperature service..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main function
main() {
    print_status "Initializing temperature service..."
    
    # Run checks
    check_service_directory
    check_venv
    check_env_file
    check_main_file
    activate_venv
    check_dependencies
    check_database
    check_1wire
    
    print_success "All checks passed!"
    echo
    
    # Start the service
    start_service
}

# Run main function
main "$@" 