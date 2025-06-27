"""
Smoke test for Core service API to validate test foundation.

This single test validates that:
- Database fixtures work correctly
- Authentication is properly configured
- FastAPI test client is functioning
- Core service endpoints are accessible
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.models import User
from shared.core.config import settings
from shared.core.security import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_auth_me_endpoint_success(client: AsyncClient, auth_headers: dict):
    """
    Test the /api/users/me endpoint to validate the entire test setup.
    
    This smoke test ensures:
    - Database isolation is working
    - Authentication headers are properly generated
    - FastAPI test client can make authenticated requests
    - Core service endpoints respond correctly
    """
    # Make a GET request to the /api/users/me endpoint
    response = await client.get("/api/users/me", headers=auth_headers)
    
    # Assert that the response status code is 200
    assert response.status_code == 200
    
    # Get the response data
    data = response.json()
    
    # Assert that the returned JSON includes the correct username
    assert data["username"] == "testadmin"


@pytest.mark.asyncio
async def test_user_registration_success(client: AsyncClient, db_session: AsyncSession):
    """
    Test successful user registration.
    
    Validates:
    - New user can be registered with valid data
    - Response contains access token
    - User is actually created in database
    """
    # Prepare registration data
    registration_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword123"
    }
    
    # Send POST request to registration endpoint
    response = await client.post("/api/auth/register", json=registration_data)
    
    # Assert successful registration
    assert response.status_code == 200
    
    # Get response data
    data = response.json()
    
    # Assert access token is returned
    assert "access_token" in data
    assert data["access_token"] is not None
    
    # Query database to verify user was created
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "newuser"))
    user = result.scalar_one_or_none()
    
    # Assert user exists in database
    assert user is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.is_admin is False  # New users should not be admin by default


@pytest.mark.asyncio
async def test_user_registration_conflict(client: AsyncClient, test_user: dict):
    """
    Test user registration with conflicting username.
    
    Validates:
    - Registration fails when username already exists
    - Appropriate error response is returned
    """
    # Prepare registration data with existing username
    registration_data = {
        "username": "testadmin",  # This username already exists from test_user fixture
        "email": "conflict@example.com",
        "password": "newpassword123"
    }
    
    # Send POST request to registration endpoint
    response = await client.post("/api/auth/register", json=registration_data)
    
    # Assert registration conflict
    assert response.status_code == 400
    
    # Get response data
    data = response.json()
    
    # Assert appropriate error message
    assert "detail" in data
    # The exact error message may vary, but should indicate username conflict


@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient, test_user: dict):
    """
    Test successful user login.
    
    Validates:
    - User can login with correct credentials
    - Access token is returned
    - Response format is correct
    """
    # Prepare login data with correct credentials
    login_data = {
        "username": test_user["user"].username,
        "password": test_user["password"]  # Use the plaintext password from fixture
    }
    
    # Send POST request to login endpoint
    response = await client.post("/api/auth/login", data=login_data)
    
    # Assert successful login
    assert response.status_code == 200
    
    # Get response data
    data = response.json()
    
    # Assert access token is returned
    assert "access_token" in data
    assert data["access_token"] is not None
    
    # Assert token type is specified
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_user_login_bad_password(client: AsyncClient, test_user: dict):
    """
    Test user login with incorrect password.
    
    Validates:
    - Login fails with incorrect password
    - Appropriate error response is returned
    """
    # Prepare login data with incorrect password
    login_data = {
        "username": test_user["user"].username,
        "password": "wrongpassword123"
    }
    
    # Send POST request to login endpoint
    response = await client.post("/api/auth/login", data=login_data)
    
    # Assert login failure
    assert response.status_code == 401
    
    # Get response data
    data = response.json()
    
    # Assert appropriate error message
    assert "detail" in data
    # The exact error message may vary, but should indicate authentication failure


@pytest.mark.asyncio
async def test_get_user_me_endpoint(client: AsyncClient, auth_headers: dict, test_user: dict):
    """
    Test GET /api/users/me endpoint.
    
    Validates:
    - Authenticated user can retrieve their own profile
    - Response contains correct user data
    """
    # Make a GET request to the /api/users/me endpoint
    response = await client.get("/api/users/me", headers=auth_headers)
    
    # Assert successful response
    assert response.status_code == 200
    
    # Get response data
    data = response.json()
    
    # Assert user data is correct
    assert data["username"] == test_user["user"].username
    assert data["email"] == test_user["user"].email
    assert data["is_admin"] == test_user["user"].is_admin
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_users_list_admin_access(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """
    Test GET /api/users/ endpoint with admin access.
    
    Validates:
    - Admin can retrieve list of all users
    - Response is a list containing user data
    """
    # Make a GET request to the /api/users/ endpoint
    response = await client.get("/api/users/", headers=auth_headers)
    
    # Assert successful response
    assert response.status_code == 200
    
    # Get response data
    data = response.json()
    
    # Assert response is a list
    assert isinstance(data, list)
    
    # Assert list contains at least one user (the test admin user)
    assert len(data) >= 1
    
    # Verify the test admin user is in the list
    admin_user = next((user for user in data if user["username"] == "testadmin"), None)
    assert admin_user is not None
    assert admin_user["is_admin"] is True


@pytest.mark.asyncio
async def test_patch_user_admin_access(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """
    Test PATCH /api/users/{user_id} endpoint with admin access.
    
    Validates:
    - Admin can update another user's data
    - Changes are reflected in the response
    - Database is updated correctly
    """
    # Create a target user to update
    target_user = User(
        username="targetuser",
        email="target@example.com",
        hashed_password=get_password_hash("targetpass"),
        is_admin=False
    )
    db_session.add(target_user)
    await db_session.commit()
    await db_session.refresh(target_user)
    
    # Prepare update data with multiple field changes
    update_data = {
        "email": "updated@example.com",
        "is_active": False,
        "is_admin": True
    }
    
    # Send PATCH request to update the target user
    response = await client.patch(f"/api/users/{target_user.id}", json=update_data, headers=auth_headers)
    
    # Assert successful update
    assert response.status_code == 200
    
    # Get response data
    data = response.json()
    
    # Assert all changes are reflected in response
    assert data["email"] == "updated@example.com"
    assert data["is_active"] is False
    assert data["is_admin"] is True
    assert data["username"] == "targetuser"  # Username should remain unchanged
    
    # Verify changes in database
    await db_session.refresh(target_user)
    assert target_user.email == "updated@example.com"
    assert target_user.is_active is False
    assert target_user.is_admin is True


@pytest.mark.asyncio
async def test_delete_user_admin_access(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """
    Test DELETE /api/users/{user_id} endpoint with admin access.
    
    Validates:
    - Admin can delete another user
    - User is removed from database
    - Appropriate response status is returned
    """
    # Create a target user to delete
    target_user = User(
        username="deleteuser",
        email="delete@example.com",
        hashed_password=get_password_hash("deletepass"),
        is_admin=False
    )
    db_session.add(target_user)
    await db_session.commit()
    await db_session.refresh(target_user)
    
    # Store the user ID for verification
    user_id = target_user.id
    
    # Send DELETE request to remove the target user
    response = await client.delete(f"/api/users/{user_id}", headers=auth_headers)
    
    # Assert successful deletion (200 or 204)
    assert response.status_code in [200, 204]
    
    # Verify user is removed from database
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.id == user_id))
    deleted_user = result.scalar_one_or_none()
    assert deleted_user is None


@pytest.mark.asyncio
async def test_admin_endpoints_as_non_admin_forbidden(client: AsyncClient, db_session: AsyncSession):
    """
    Test that non-admin users are forbidden from accessing admin-only endpoints.
    
    Validates:
    - Non-admin users cannot access admin endpoints
    - Appropriate 403 Forbidden response is returned
    """
    # Create a non-admin user
    non_admin_user = User(
        username="nonadmin",
        email="nonadmin@example.com",
        hashed_password=get_password_hash("nonadminpass"),
        is_admin=False
    )
    db_session.add(non_admin_user)
    await db_session.commit()
    await db_session.refresh(non_admin_user)
    
    # Generate authentication token for non-admin user
    non_admin_token = create_access_token(data={"sub": non_admin_user.username})
    non_admin_headers = {"Authorization": f"Bearer {non_admin_token}"}
    
    # Attempt to access admin-only endpoint with non-admin token
    response = await client.get("/api/users/", headers=non_admin_headers)
    
    # Assert access is forbidden
    assert response.status_code == 403
    
    # Get response data
    data = response.json()
    
    # Assert appropriate error message
    assert "detail" in data
    # The exact error message may vary, but should indicate insufficient permissions 