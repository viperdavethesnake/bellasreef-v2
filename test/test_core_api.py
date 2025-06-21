import os
import requests
from pathlib import Path

BASE_URL = "http://192.168.33.122:8000"
ENV_PATH = Path(__file__).resolve().parent.parent / "core" / ".env.example"

def parse_env_example():
    username = "admin"
    password = "admin"
    try:
        with open(ENV_PATH, "r") as f:
            for line in f:
                if line.startswith("ADMIN_USERNAME="):
                    username = line.strip().split("=", 1)[1]
                if line.startswith("ADMIN_PASSWORD="):
                    password = line.strip().split("=", 1)[1]
    except Exception as e:
        print(f"Warning: Couldn't read {ENV_PATH}, using defaults: {e}")
    return username, password

def get_admin_token(username, password):
    login_data = {
        "username": username,
        "password": password
    }
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    print("✅ Login endpoint passed")
    return data["access_token"]

def test_health_check():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    print("✅ Health check passed")

def test_root_endpoint():
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    data = r.json()
    assert "service" in data
    assert "version" in data
    print("✅ Root endpoint passed")

def test_protected_endpoint_with_token(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "username" in data
    print("✅ Protected endpoint (/api/users/me) passed")

def test_protected_endpoint_without_token():
    r = requests.get(f"{BASE_URL}/api/users/me")
    assert r.status_code == 401
    data = r.json()
    assert "detail" in data
    print("✅ Protected endpoint (no token) passed")

def test_admin_endpoint(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/users/", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    print("✅ Admin endpoint (/api/users/) passed")

def test_core_api_workflow():
    print("Testing Core API endpoints...\n")
    username, password = parse_env_example()
    print(f"Using admin credentials from {ENV_PATH}: {username} / {password}")
    test_health_check()
    test_root_endpoint()
    token = get_admin_token(username, password)
    test_protected_endpoint_with_token(token)
    test_protected_endpoint_without_token()
    test_admin_endpoint(token)
    print("\n🎉 All Core API tests completed successfully!")

if __name__ == "__main__":
    test_core_api_workflow()
