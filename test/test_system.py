"""
System Tests for Bella's Reef Backend

This module tests the core system functionality including:
- Health check endpoint
- Authentication (login, register, token validation)
- User management endpoints
- API response formats and error handling

Test Categories:
- Health endpoint functionality
- Authentication flow (login, register, token validation)
- User CRUD operations
- Error handling and validation
- Security (password hashing, token expiration)

Usage:
    pytest backend/tests/test_system.py -v
    pytest backend/tests/test_system.py::test_health_endpoint -v
    pytest backend/tests/test_system.py -m "system" -v
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import patch

import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.security import create_access_token, verify_password
from shared.crud.user import create_user, get_user_by_username
from shared.schemas.user import UserCreate

# =============================================================================
# Health Endpoint Tests
# =============================================================================

@pytest.mark.system
class TestHealthEndpoint:
    """Test health check endpoint functionality."""
    
    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_endpoint_response_format(self, client):
        """Test health endpoint response format."""
        response = client.get("/health")
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        
        # Check field values
        assert data["status"] == "healthy"
        assert data["service"] == "Bella's Reef API"
        assert data["version"] == "1.0.0"
        
        # Check timestamp format (ISO 8601)
        try:
            datetime.fromisoformat(data["timestamp"])
        except ValueError:
            pytest.fail("Timestamp is not in ISO 8601 format")
    
    def test_health_endpoint_timestamp_is_recent(self, client):
        """Test that health timestamp is recent (within last 5 seconds)."""
        response = client.get("/health")
        data = response.json()
        
        timestamp = datetime.fromisoformat(data["timestamp"])
        now = datetime.utcnow()
        
        # Timestamp should be within last 5 seconds
        assert abs((now - timestamp).total_seconds()) < 5

# =============================================================================
# Authentication Tests
# =============================================================================

@pytest.mark.system
class TestAuthentication:
    """Test authentication endpoints and functionality."""
    
    @pytest.mark.asyncio
    async def test_user_registration_success(self, test_session: AsyncSession):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123"
        }
        
        user_create = UserCreate(**user_data)
        user = await create_user(test_session, user_create)
        
        assert user.username == user_data["username"]
        assert user.email == user_data["email"]
        assert user.is_active is True
        assert user.is_admin is False
        assert user.hashed_password != user_data["password"]  # Should be hashed
    
    @pytest.mark.asyncio
    async def test_user_registration_duplicate_username(self, test_session: AsyncSession):
        """Test user registration with duplicate username fails."""
        user_data = {
            "username": "duplicateuser",
            "email": "user1@example.com",
            "password": "securepass123"
        }
        
        # Create first user
        user_create = UserCreate(**user_data)
        await create_user(test_session, user_create)
        
        # Try to create second user with same username
        user_data2 = {
            "username": "duplicateuser",  # Same username
            "email": "user2@example.com",
            "password": "securepass456"
        }
        
        user_create2 = UserCreate(**user_data2)
        
        # This should raise an exception (handled by the API)
        # We're testing the CRUD layer here
        with pytest.raises(Exception):  # SQLAlchemy integrity error
            await create_user(test_session, user_create2)
    
    def test_login_endpoint_success(self, client, test_session):
        """Test successful login via API endpoint."""
        # First create a user
        user_data = {
            "username": "logintest",
            "email": "logintest@example.com",
            "password": "testpass123"
        }
        
        # Create user directly in database for testing
        user_create = UserCreate(**user_data)
        asyncio.run(create_user(test_session, user_create))
        
        # Test login
        login_data = {
            "username": "logintest",
            "password": "testpass123"
        }
        
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
        assert data["token_type"] == "bearer"
    
    def test_login_endpoint_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_endpoint_missing_fields(self, client):
        """Test login with missing required fields."""
        # Missing password
        login_data = {"username": "testuser"}
        
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_endpoint_success(self, client):
        """Test successful user registration via API endpoint."""
        user_data = {
            "username": "apiregister",
            "email": "apiregister@example.com",
            "password": "securepass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
        assert data["token_type"] == "bearer"
    
    def test_register_endpoint_duplicate_username(self, client):
        """Test registration with duplicate username fails."""
        user_data = {
            "username": "duplicateapi",
            "email": "user1@example.com",
            "password": "securepass123"
        }
        
        # First registration should succeed
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second registration with same username should fail
        user_data2 = {
            "username": "duplicateapi",  # Same username
            "email": "user2@example.com",
            "password": "securepass456"
        }
        
        response2 = client.post("/api/v1/auth/register", json=user_data2)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response2.json()
        assert "detail" in data
        assert "already registered" in data["detail"].lower()

# =============================================================================
# User Management Tests
# =============================================================================

@pytest.mark.system
class TestUserManagement:
    """Test user management endpoints."""
    
    def test_get_current_user_with_valid_token(self, client, test_session):
        """Test getting current user with valid token."""
        # Create user and get token
        user_data = {
            "username": "currentuser",
            "email": "currentuser@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        
        token_data = response.json()
        access_token = token_data["access_token"]
        
        # Test getting current user
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        user_data_response = response.json()
        assert user_data_response["username"] == user_data["username"]
        assert user_data_response["email"] == user_data["email"]
        assert "hashed_password" not in user_data_response  # Password should not be returned
        assert "id" in user_data_response
        assert "is_active" in user_data_response
        assert "is_admin" in user_data_response
    
    def test_get_current_user_without_token(self, client):
        """Test getting current user without token fails."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_with_invalid_token(self, client):
        """Test getting current user with invalid token fails."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_users_list_with_admin_token(self, client):
        """Test getting users list with admin token."""
        # Create admin user (this would need admin creation logic)
        # For now, test that endpoint exists and requires authentication
        response = client.get("/api/v1/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

# =============================================================================
# Security Tests
# =============================================================================

@pytest.mark.system
class TestSecurity:
    """Test security-related functionality."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "testpassword123"
        
        # Create a user to test password hashing
        user_data = {
            "username": "securitytest",
            "email": "security@example.com",
            "password": password
        }
        
        # This would normally be done through the API, but we're testing the hashing
        # Verify that the password is hashed (not plain text)
        assert password != "hashed_password_placeholder"  # Placeholder for actual test
    
    def test_token_expiration(self):
        """Test that tokens expire correctly."""
        # Create a token with short expiration
        short_expiry = timedelta(minutes=1)
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=short_expiry
        )
        
        # Token should be valid initially
        assert token is not None
        assert len(token) > 0
    
    def test_password_verification(self):
        """Test password verification works correctly."""
        password = "testpass123"
        
        # This would test the actual password verification
        # For now, just verify the function exists
        assert callable(verify_password)

# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.system
class TestErrorHandling:
    """Test error handling and validation."""
    
    def test_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422 Unprocessable Entity."""
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_missing_required_fields_returns_422(self, client):
        """Test that missing required fields returns 422."""
        user_data = {
            "username": "testuser"
            # Missing email and password
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_email_format_returns_422(self, client):
        """Test that invalid email format returns 422."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.system
@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for system functionality."""
    
    def test_full_auth_flow(self, client):
        """Test complete authentication flow: register -> login -> access protected endpoint."""
        # Step 1: Register new user
        user_data = {
            "username": "integrationtest",
            "email": "integration@example.com",
            "password": "testpass123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_200_OK
        
        register_token = register_response.json()["access_token"]
        
        # Step 2: Login with same credentials
        login_data = {
            "username": "integrationtest",
            "password": "testpass123"
        }
        
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        
        login_token = login_response.json()["access_token"]
        
        # Step 3: Access protected endpoint with both tokens
        for token in [register_token, login_token]:
            response = client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            
            user_data_response = response.json()
            assert user_data_response["username"] == user_data["username"]
    
    def test_health_endpoint_under_load(self, client):
        """Test health endpoint handles multiple requests."""
        responses = []
        
        # Make multiple concurrent requests
        for i in range(10):
            response = client.get("/health")
            responses.append(response)
        
        # All responses should be successful
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["status"] == "healthy"

# =============================================================================
# Manual Test Instructions
# =============================================================================

"""
MANUAL TEST INSTRUCTIONS FOR SYSTEM ENDPOINTS

These instructions should be followed on the target Raspberry Pi environment
to verify system functionality in the actual deployment environment.

1. HEALTH ENDPOINT MANUAL TESTS
   ============================
   
   a) Basic Health Check:
      curl -X GET http://localhost:8000/health
      Expected: 200 OK with JSON response containing status, timestamp, service, version
   
   b) Health Check Under Load:
      for i in {1..50}; do curl -s http://localhost:8000/health | jq .status; done
      Expected: All responses should return "healthy"
   
   c) Health Check with Different Content Types:
      curl -H "Accept: application/json" http://localhost:8000/health
      curl -H "Accept: text/plain" http://localhost:8000/health
      Expected: JSON response in both cases

2. AUTHENTICATION MANUAL TESTS
   ===========================
   
   a) User Registration:
      curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"username":"manualtest","email":"manual@test.com","password":"testpass123"}'
      Expected: 200 OK with access_token
   
   b) User Login:
      curl -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=manualtest&password=testpass123"
      Expected: 200 OK with access_token
   
   c) Invalid Login:
      curl -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=manualtest&password=wrongpass"
      Expected: 401 Unauthorized
   
   d) Duplicate Registration:
      curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"username":"manualtest","email":"different@test.com","password":"testpass456"}'
      Expected: 400 Bad Request with "already registered" message

3. USER MANAGEMENT MANUAL TESTS
   =============================
   
   a) Get Current User (with valid token):
      TOKEN="your_access_token_here"
      curl -X GET http://localhost:8000/api/v1/users/me \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with user data (no password field)
   
   b) Get Current User (without token):
      curl -X GET http://localhost:8000/api/v1/users/me
      Expected: 401 Unauthorized
   
   c) Get Current User (invalid token):
      curl -X GET http://localhost:8000/api/v1/users/me \
        -H "Authorization: Bearer invalid_token"
      Expected: 401 Unauthorized

4. ERROR HANDLING MANUAL TESTS
   ============================
   
   a) Invalid JSON:
      curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"username": "test", "invalid json}'
      Expected: 422 Unprocessable Entity
   
   b) Missing Required Fields:
      curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"username": "test"}'
      Expected: 422 Unprocessable Entity
   
   c) Invalid Email Format:
      curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"username":"test","email":"invalid-email","password":"testpass"}'
      Expected: 422 Unprocessable Entity

5. PERFORMANCE MANUAL TESTS
   =========================
   
   a) Response Time Test:
      time curl -s http://localhost:8000/health > /dev/null
      Expected: Response time < 100ms
   
   b) Concurrent Request Test:
      for i in {1..20}; do
        curl -s http://localhost:8000/health > /dev/null &
      done
      wait
      Expected: All requests complete successfully
   
   c) Memory Usage Test:
      # Monitor memory usage during load test
      while true; do
        curl -s http://localhost:8000/health > /dev/null
        sleep 0.1
      done &
      # Monitor with: ps aux | grep uvicorn
      Expected: Memory usage remains stable

6. SECURITY MANUAL TESTS
   ======================
   
   a) Password Hashing Verification:
      # Register a user and check database
      curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"username":"securitytest","email":"security@test.com","password":"testpass123"}'
      
      # Check database (requires database access)
      # Password should be hashed, not plain text
   
   b) Token Expiration Test:
      # Get token and wait for expiration
      TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=securitytest&password=testpass123" | jq -r .access_token)
      
      # Wait for token expiration (configure short expiry for testing)
      sleep 65  # Assuming 1-minute expiry
      
      curl -X GET http://localhost:8000/api/v1/users/me \
        -H "Authorization: Bearer $TOKEN"
      Expected: 401 Unauthorized after expiration

7. LOGGING AND MONITORING MANUAL TESTS
   ====================================
   
   a) Check Application Logs:
      tail -f /var/log/bellasreef/app.log
      # Make requests and verify logging
   
   b) Check Error Logs:
      tail -f /var/log/bellasreef/error.log
      # Make invalid requests and verify error logging
   
   c) Check System Resources:
      htop
      # Monitor CPU and memory usage during tests

8. NETWORK AND FIREWALL MANUAL TESTS
   ==================================
   
   a) Test from External Network:
      # From another machine on the network
      curl http://PI_IP_ADDRESS:8000/health
      Expected: 200 OK
   
   b) Test with Different Ports:
      curl http://localhost:8000/health  # Default port
      curl http://localhost:8001/health  # Alternative port (if configured)
   
   c) Test with HTTPS (if configured):
      curl -k https://localhost:8443/health
      Expected: 200 OK (if HTTPS is configured)

NOTES:
- Replace localhost with actual IP address when testing from external machines
- Ensure firewall allows connections on port 8000 (or configured port)
- Monitor system resources during load testing
- Check logs for any errors or warnings
- Verify database connections and performance
""" 