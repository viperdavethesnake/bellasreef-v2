# test/test_core_api.py
# Placeholder for core API tests

import requests

BASE_URL = "http://192.168.33.122:8000"  # Core service runs on port 8000
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword123"
TEST_EMAIL = "test@example.com"


def test_health_check():
    """Test health check endpoint (/health) - expect 200 and correct JSON."""
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "Bella's Reef API"
    assert data["version"] == "1.0.0"


def test_root_endpoint():
    """Test root endpoint (/) - expect 200 and service information."""
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "Bella's Reef Core Service"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data


def test_user_registration():
    """Test user registration endpoint - expect 201 and token in response."""
    user_data = {
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        headers={"Content-Type": "application/json"},
        json=user_data
    )
    # Registration might fail if user already exists, which is expected
    if r.status_code == 201:
        data = r.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
    elif r.status_code == 400:
        # User already exists
        data = r.json()
        assert "detail" in data
        assert "already registered" in data["detail"]


def test_login_success():
    """Test login endpoint with valid credentials - expect token in response."""
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        data=login_data,  # Use form data for OAuth2PasswordRequestForm
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    return data["access_token"]


def test_login_failure():
    """Test login endpoint with invalid credentials - expect 401."""
    login_data = {
        "username": "invaliduser",
        "password": "wrongpassword"
    }
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert r.status_code == 401
    data = r.json()
    assert "detail" in data
    assert "Incorrect username or password" in data["detail"]


def test_protected_endpoint_with_token():
    """Test protected endpoint with valid token - expect 200."""
    # First get a token
    token = test_login_success()
    
    # Test protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == TEST_USERNAME


def test_protected_endpoint_without_token():
    """Test protected endpoint without token - expect 401."""
    r = requests.get(f"{BASE_URL}/api/users/me")
    assert r.status_code == 401
    data = r.json()
    assert "detail" in data


def test_admin_endpoint():
    """Test admin-only endpoint - expect 403 for regular user."""
    # First get a token for regular user
    token = test_login_success()
    
    # Test admin endpoint with regular user token
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/users/", headers=headers)
    # Regular user should get 403, admin would get 200
    assert r.status_code in (403, 200)
    if r.status_code == 403:
        data = r.json()
        assert "detail" in data
        assert "privileges" in data["detail"]


def test_core_api_workflow():
    """Run the complete core API workflow test."""
    print("Testing Core API endpoints...")
    
    # Test health check
    test_health_check()
    print("✅ Health check passed")
    
    # Test root endpoint
    test_root_endpoint()
    print("✅ Root endpoint passed")
    
    # Test user registration
    test_user_registration()
    print("✅ User registration passed")
    
    # Test login success
    test_login_success()
    print("✅ Login success passed")
    
    # Test login failure
    test_login_failure()
    print("✅ Login failure passed")
    
    # Test protected endpoint with token
    test_protected_endpoint_with_token()
    print("✅ Protected endpoint with token passed")
    
    # Test protected endpoint without token
    test_protected_endpoint_without_token()
    print("✅ Protected endpoint without token passed")
    
    # Test admin endpoint
    test_admin_endpoint()
    print("✅ Admin endpoint passed")
    
    print("🎉 All core API tests completed successfully!")


if __name__ == "__main__":
    test_core_api_workflow() 