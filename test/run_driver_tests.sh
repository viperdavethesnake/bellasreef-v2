#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# The project root is one level up
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Add the project root to the Python path for this script's execution
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "Project root added to PYTHONPATH: $PROJECT_ROOT"

#
# Bella's Reef - PCA9685 Driver Test Runner
#
# Description: Runs unit tests for the PCA9685 hardware driver
# Usage: ./run_driver_tests.sh
#

set -euo pipefail
IFS=$'\n\t'

# Script directory for relative path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# =============================================================================
# COLOR AND STYLE DEFINITIONS
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🧪 PCA9685 Driver Test Suite 🧪                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section_header() {
    local title="$1"
    echo -e "\n${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  ${title}${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_subsection() {
    local title="$1"
    echo -e "\n${PURPLE}${BOLD}▶ ${title}${NC}"
}

print_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ ${1}${NC}"
}

print_progress() {
    local message="$1"
    echo -n -e "${CYAN}⏳ ${message}...${NC}"
}

print_progress_done() {
    echo -e "${GREEN} Done.${NC}"
}

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

check_environment() {
    print_subsection "Environment Validation"
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file not found, using default settings"
    else
        print_progress "Loading environment variables"
        source "$PROJECT_ROOT/.env"
        print_progress_done
    fi
}

activate_venv() {
    print_subsection "Virtual Environment Setup"
    
    if [ ! -d "$PROJECT_ROOT/bellasreef-venv" ]; then
        print_error "Virtual environment not found at $PROJECT_ROOT/bellasreef-venv"
        echo -e "${WHITE}   Please run the setup script first.${NC}"
        exit 1
    fi
    
    print_progress "Activating virtual environment"
    source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
    print_progress_done
}

check_dependencies() {
    print_subsection "Dependency Check"
    
    print_progress "Checking pytest installation"
    if ! python -c "import pytest" 2>/dev/null; then
        print_error "pytest not found. Installing..."
        pip install pytest pytest-mock
    else
        print_progress_done
    fi
    
    print_progress "Checking pytest-mock installation"
    if ! python -c "import pytest_mock" 2>/dev/null; then
        print_error "pytest-mock not found. Installing..."
        pip install pytest-mock
    else
        print_progress_done
    fi
}

run_tests() {
    print_subsection "Running PCA9685 Driver Tests"
    
    cd "$PROJECT_ROOT"
    
    print_info "Test file: test/test_driver_pca9685.py"
    print_info "Test coverage:"
    echo -e "  • I2C bus context manager"
    echo -e "  • Board detection (check_board)"
    echo -e "  • Frequency setting (set_frequency)"
    echo -e "  • Duty cycle control (set_channel_duty_cycle)"
    echo -e "  • Duty cycle reading (get_current_duty_cycle)"
    echo -e "  • Edge cases and error handling"
    echo ""
    
    print_progress "Executing tests with pytest"
    if pytest test/test_driver_pca9685.py -v --tb=short; then
        print_progress_done
        print_success "All tests passed!"
    else
        print_error "Some tests failed. Check the output above for details."
        exit 1
    fi
}

run_coverage() {
    print_subsection "Code Coverage Analysis"
    
    print_progress "Checking coverage tools"
    if ! python -c "import coverage" 2>/dev/null; then
        print_warning "coverage not installed. Installing..."
        pip install coverage
    else
        print_progress_done
    fi
    
    print_progress "Running tests with coverage"
    if coverage run -m pytest test/test_driver_pca9685.py; then
        print_progress_done
        print_success "Coverage analysis complete!"
        
        print_progress "Generating coverage report"
        coverage report -m --include="hal/drivers/pca9685_driver.py"
        print_progress_done
    else
        print_error "Coverage analysis failed."
        exit 1
    fi
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    print_banner
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Setup and validation
    check_environment
    activate_venv
    check_dependencies
    
    # Run tests
    run_tests
    
    # Optional: Run coverage analysis
    if [ "${1:-}" = "--coverage" ]; then
        run_coverage
    fi
    
    print_section_header "🎉 PCA9685 Driver Test Suite Completed Successfully! 🎉"
    echo -e "${WHITE}📋 Summary:${NC}"
    echo -e "  • All unit tests passed"
    echo -e "  • Hardware interactions properly mocked"
    echo -e "  • Error handling scenarios tested"
    echo -e "  • Edge cases covered"
    echo ""
    echo -e "${CYAN}💡 Tip: Run with --coverage flag for detailed coverage analysis${NC}"
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@" 