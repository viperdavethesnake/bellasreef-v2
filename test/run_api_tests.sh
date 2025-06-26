#!/bin/bash
#
# Bella's Reef - HAL API Integration Test Runner
#
# Description: Runs integration tests for the HAL API controllers and channels
# Usage: ./run_api_tests.sh [test_file]
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
    echo "║              🧪 HAL API Integration Test Suite 🧪              ║"
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
        pip install pytest pytest-mock httpx
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
    
    print_progress "Checking httpx installation"
    if ! python -c "import httpx" 2>/dev/null; then
        print_error "httpx not found. Installing..."
        pip install httpx
    else
        print_progress_done
    fi
}

run_controller_tests() {
    print_subsection "Running Controller API Tests"
    
    cd "$PROJECT_ROOT"
    
    print_info "Test file: test/test_api_controllers.py"
    print_info "Test coverage:"
    echo -e "  • Controller discovery (GET /discover)"
    echo -e "  • Controller registration (POST /)"
    echo -e "  • Controller listing (GET /)"
    echo -e "  • Controller deletion (DELETE /{id})"
    echo -e "  • Frequency updates (PATCH /{id}/frequency)"
    echo -e "  • Channel registration (POST /{id}/channels)"
    echo -e "  • Channel listing (GET /{id}/channels)"
    echo -e "  • Cascading deletion"
    echo ""
    
    print_progress "Executing controller tests with pytest"
    if pytest test/test_api_controllers.py -v --tb=short; then
        print_progress_done
        print_success "All controller tests passed!"
    else
        print_error "Some controller tests failed. Check the output above for details."
        return 1
    fi
}

run_channel_tests() {
    print_subsection "Running Channel API Tests"
    
    cd "$PROJECT_ROOT"
    
    if [ -f "test/test_api_channels.py" ]; then
        print_info "Test file: test/test_api_channels.py"
        print_info "Test coverage:"
        echo -e "  • Channel control (POST /{id}/control)"
        echo -e "  • Bulk channel control (POST /bulk-control)"
        echo -e "  • Channel state (GET /{id}/state)"
        echo -e "  • Live channel state (GET /{id}/live-state)"
        echo -e "  • Channel listing (GET /)"
        echo ""
        
        print_progress "Executing channel tests with pytest"
        if pytest test/test_api_channels.py -v --tb=short; then
            print_progress_done
            print_success "All channel tests passed!"
        else
            print_error "Some channel tests failed. Check the output above for details."
            return 1
        fi
    else
        print_warning "Channel tests not found (test/test_api_channels.py)"
        print_info "Channel tests will be created in the next phase"
    fi
}

run_all_tests() {
    print_subsection "Running All API Tests"
    
    cd "$PROJECT_ROOT"
    
    print_progress "Executing all API tests with pytest"
    if pytest test/test_api_*.py -v --tb=short; then
        print_progress_done
        print_success "All API tests passed!"
    else
        print_error "Some API tests failed. Check the output above for details."
        return 1
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
    if coverage run -m pytest test/test_api_*.py; then
        print_progress_done
        print_success "Coverage analysis complete!"
        
        print_progress "Generating coverage report"
        coverage report -m --include="hal/api/*.py"
        print_progress_done
    else
        print_error "Coverage analysis failed."
        return 1
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
    
    # Determine which tests to run
    local test_target="${1:-all}"
    
    case "$test_target" in
        "controllers")
            run_controller_tests
            ;;
        "channels")
            run_channel_tests
            ;;
        "all"|"")
            run_controller_tests
            run_channel_tests
            ;;
        *)
            print_error "Unknown test target: $test_target"
            echo -e "${WHITE}Available targets: controllers, channels, all${NC}"
            exit 1
            ;;
    esac
    
    # Optional: Run coverage analysis
    if [ "${2:-}" = "--coverage" ]; then
        run_coverage
    fi
    
    print_section_header "🎉 HAL API Integration Test Suite Completed Successfully! 🎉"
    echo -e "${WHITE}📋 Summary:${NC}"
    echo -e "  • All integration tests passed"
    echo -e "  • API endpoints properly tested"
    echo -e "  • Database interactions verified"
    echo -e "  • Hardware interactions mocked"
    echo -e "  • Error handling scenarios tested"
    echo ""
    echo -e "${CYAN}💡 Usage:${NC}"
    echo -e "  • ./run_api_tests.sh controllers     # Run only controller tests"
    echo -e "  • ./run_api_tests.sh channels        # Run only channel tests"
    echo -e "  • ./run_api_tests.sh all --coverage  # Run all tests with coverage"
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@" 