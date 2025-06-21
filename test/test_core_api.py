#!/usr/bin/env python3
import requests
from pathlib import Path
import re

BASE_URL = "http://192.168.33.122:8000"

def get_admin_credentials():
    """Reads admin credentials from core/env.example or uses defaults if not found."""
    ENV_PATH = Path(__file__).resolve().parent.parent / "core" / "env.example"
    username = "admin"
    password = "admin"
    try:
        with open(ENV_PATH) as f:
            env = f.read()
        user_match = re.search(r"^ADMIN_USERNAME\s*=\s*(\S+)", env, re.MULTILINE)
        pass_match = re.search(r"^ADMIN_PASSWORD\s*=\s*(\S+)", env, re.MULTILINE)
        if user_match:
            username = user_match.group(1)
        if pass_match:
            password = pass_match.group(1)
        print(f"Using admin credentials from {ENV_PATH}: {username} / {password}")
    except Exception as e:
        print(f"Warning: Couldn't read {ENV_PATH}, using defaults: {e}")
    return username, password

def test_health_check():
    print("➡️  Testing /health ...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"/health failed: {r.status_code} {r.text}"
    print("✅ Health check passed")

def test_root_endpoint():
    print("➡️  Testing / (root) ...")
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Root endpoint failed: {r.status_code} {r.text}"
    print("✅ Root endpoint passed")

def test_login_success(username, password):
    print("➡️  Testing /api/auth/auth/login ...")
    login_data = {
        "username": username,
        "password": password,
    }
    r = requests.post(
        f"{BASE_URL}/api/auth/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    print("✅ Login success passed")
    return data["access_token"]

def test_get_current_user(token, username):
    print("➡️  Testing /api/users/users/me ...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/users/users/me", headers=headers)
    assert r.status_code == 200, f"Get current user failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("username") == username
    print("✅ Get current user passed")

def test_admin_get_users(token):
    print("➡️  Testing /api/users/users/ (admin users list) ...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/users/users/", headers=headers)
    assert r.status_code == 200, f"Admin get users failed: {r.status_code} {r.text}"
    data = r.json()
    assert isinstance(data, list)
    print("✅ Admin get users passed")

def test_protected_endpoint_without_token():
    print("➡️  Testing protected endpoint without token ...")
    r = requests.get(f"{BASE_URL}/api/users/users/me")
    assert r.status_code == 401, f"Protected endpoint should fail without token, got: {r.status_code} {r.text}"
    print("✅ Protected endpoint without token passed")

def test_core_api_workflow():
    print("Testing Core API endpoints...\n")
    username, password = get_admin_credentials()
    test_health_check()
    test_root_endpoint()
    token = test_login_success(username, password)
    test_get_current_user(token, username)
    test_admin_get_users(token)
    test_protected_endpoint_without_token()
    print("\n🎉 All Core API tests completed successfully!")

if __name__ == "__main__":
    test_core_api_workflow()
