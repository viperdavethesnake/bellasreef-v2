#!/bin/bash
#
# Bella's Reef - SmartOutlets API Service Test Script
#
# Description: Tests the SmartOutlets API service endpoints to verify functionality.
# Date: 2025-06-22
# Author: Bella's Reef Development Team

set -euo pipefail
IFS=$'\n\t'

# Script directory for relative path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# =============================================================================
# FUNCTIONS
# =============================================================================

check_environment() {
    """Check if .env file exists and load environment variables."""
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "❌ Error: .env file not found in project root!"
        echo "   Please copy env.example to .env and configure your settings."
        exit 1
    fi
    
    # Load environment variables
    source "$PROJECT_ROOT/.env"
}

get_auth_token() {
    """Get authentication token from the core service."""
    echo "🔐 Getting authentication token..."
    
    local response
    response=$(curl -s -X POST "http://localhost:${SERVICE_PORT_CORE:-8000}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${ADMIN_USERNAME:-admin}&password=${ADMIN_PASSWORD:-admin}")
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "access_token"; then
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Token obtained successfully"
    else
        echo "❌ Failed to get token"
        echo "Response: $response"
        exit 1
    fi
}

test_health_endpoint() {
    """Test the health endpoint."""
    echo ""
    echo "🏥 Testing health endpoint..."
    curl -s "http://localhost:${SERVICE_PORT_SMARTOUTLETS:-8005}/health" | jq .
}

test_discover_outlets() {
    """Test the discover outlets endpoint."""
    echo ""
    echo "🔍 Testing discover outlets endpoint..."
    curl -s -H "Authorization: Bearer $TOKEN" \
        "http://localhost:${SERVICE_PORT_SMARTOUTLETS:-8005}/outlets/discover" | jq .
}

test_get_outlets() {
    """Test the get outlets endpoint."""
    echo ""
    echo "🔌 Testing get outlets endpoint..."
    curl -s -H "Authorization: Bearer $TOKEN" \
        "http://localhost:${SERVICE_PORT_SMARTOUTLETS:-8005}/outlets/" | jq .
}

print_summary() {
    """Print test summary."""
    echo ""
    echo "✅ SmartOutlets API service tests completed!"
    echo "📖 API Documentation: http://localhost:${SERVICE_PORT_SMARTOUTLETS:-8005}/docs"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to test the smartoutlets API service."""
    echo "🧪 Testing SmartOutlets API Service..."
    echo "   - Host: localhost"
    echo "   - Port: ${SERVICE_PORT_SMARTOUTLETS:-8005}"
    echo ""
    
    # Setup
    check_environment
    get_auth_token
    
    # Run tests
    test_health_endpoint
    test_discover_outlets
    test_get_outlets
    
    # Summary
    print_summary
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"


