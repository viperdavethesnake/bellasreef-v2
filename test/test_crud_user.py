"""
Unit tests for user CRUD operations.

This module tests the shared/crud/user.py functions using a temporary in-memory
SQLite database to ensure test isolation and validate database operations.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Import the database and models
from shared.db.database import Base
from shared.db.models import User
from shared.crud.user import (
    create_user, get_user, get_user_by_username, get_user_by_email,
    get_users, update_user, delete_user
)
from shared.schemas.user import UserCreate, UserUpdate
from shared.core.security import verify_password


# =============================================================================
# TEST DATABASE SETUP
# =============================================================================

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Set up the test database before each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Create a database session for testing."""
    async with TestingSessionLocal() as session:
        yield session


# =============================================================================
# TEST CASES
# =============================================================================

class TestCreateUser:
    """Test user creation functionality."""
    
    async def test_create_user_success(self, db_session):
        """Test successfully creating a user with all fields."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890",
            password="testpassword123",
            is_active=True,
            is_admin=False
        )
        
        # Create the user
        created_user = await create_user(db_session, user_data)
        
        # Verify the user was created with correct data
        assert created_user.id is not None
        assert created_user.username == user_data.username
        assert created_user.email == user_data.email
        assert created_user.phone_number == user_data.phone_number
        assert created_user.is_active == user_data.is_active
        assert created_user.is_admin == user_data.is_admin
        assert created_user.created_at is not None
        assert created_user.updated_at is not None
        
        # Verify password was hashed
        assert created_user.hashed_password != user_data.password
        assert verify_password(user_data.password, created_user.hashed_password)
    
    async def test_create_user_minimal_fields(self, db_session):
        """Test creating a user with only required fields."""
        user_data = UserCreate(
            username="minimaluser",
            email="minimal@example.com",
            password="password123"
        )
        
        created_user = await create_user(db_session, user_data)
        
        # Verify default values
        assert created_user.username == user_data.username
        assert created_user.email == user_data.email
        assert created_user.phone_number is None
        assert created_user.is_active is True  # Default value
        assert created_user.is_admin is False  # Default value
        assert verify_password(user_data.password, created_user.hashed_password)


class TestGetUser:
    """Test user retrieval functionality."""
    
    async def test_get_user_by_id_success(self, db_session):
        """Test successfully retrieving a user by ID."""
        # Create a user first
        user_data = UserCreate(
            username="getuser",
            email="get@example.com",
            password="password123"
        )
        created_user = await create_user(db_session, user_data)
        
        # Retrieve the user by ID
        retrieved_user = await get_user(db_session, created_user.id)
        
        # Verify the retrieved user matches
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == created_user.username
        assert retrieved_user.email == created_user.email
    
    async def test_get_user_by_id_not_found(self, db_session):
        """Test retrieving a non-existent user by ID."""
        retrieved_user = await get_user(db_session, 999)
        assert retrieved_user is None
    
    async def test_get_user_by_username_success(self, db_session):
        """Test successfully retrieving a user by username."""
        # Create a user first
        user_data = UserCreate(
            username="usernameuser",
            email="username@example.com",
            password="password123"
        )
        created_user = await create_user(db_session, user_data)
        
        # Retrieve the user by username
        retrieved_user = await get_user_by_username(db_session, created_user.username)
        
        # Verify the retrieved user matches
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == created_user.username
    
    async def test_get_user_by_username_not_found(self, db_session):
        """Test retrieving a non-existent user by username."""
        retrieved_user = await get_user_by_username(db_session, "nonexistent")
        assert retrieved_user is None
    
    async def test_get_user_by_email_success(self, db_session):
        """Test successfully retrieving a user by email."""
        # Create a user first
        user_data = UserCreate(
            username="emailuser",
            email="email@example.com",
            password="password123"
        )
        created_user = await create_user(db_session, user_data)
        
        # Retrieve the user by email
        retrieved_user = await get_user_by_email(db_session, created_user.email)
        
        # Verify the retrieved user matches
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    async def test_get_user_by_email_not_found(self, db_session):
        """Test retrieving a non-existent user by email."""
        retrieved_user = await get_user_by_email(db_session, "nonexistent@example.com")
        assert retrieved_user is None
    
    async def test_get_users_success(self, db_session):
        """Test retrieving all users."""
        # Create multiple users
        user1_data = UserCreate(
            username="user1",
            email="user1@example.com",
            password="password123"
        )
        user2_data = UserCreate(
            username="user2",
            email="user2@example.com",
            password="password456"
        )
        
        await create_user(db_session, user1_data)
        await create_user(db_session, user2_data)
        
        # Retrieve all users
        users = await get_users(db_session)
        
        # Verify we got the expected number of users
        assert len(users) >= 2
        
        # Verify the users we created are in the list
        usernames = [user.username for user in users]
        assert "user1" in usernames
        assert "user2" in usernames
    
    async def test_get_users_with_pagination(self, db_session):
        """Test retrieving users with pagination."""
        # Create multiple users
        for i in range(5):
            user_data = UserCreate(
                username=f"paginated{i}",
                email=f"paginated{i}@example.com",
                password="password123"
            )
            await create_user(db_session, user_data)
        
        # Test with limit
        users = await get_users(db_session, skip=0, limit=3)
        assert len(users) == 3
        
        # Test with skip
        users = await get_users(db_session, skip=2, limit=3)
        assert len(users) == 3


class TestUpdateUser:
    """Test user update functionality."""
    
    async def test_update_user_email(self, db_session):
        """Test updating a user's email."""
        # Create a user first
        user_data = UserCreate(
            username="updateuser",
            email="old@example.com",
            password="password123"
        )
        created_user = await create_user(db_session, user_data)
        
        # Update the user's email
        update_data = UserUpdate(email="new@example.com")
        updated_user = await update_user(db_session, created_user.id, update_data)
        
        # Verify the update
        assert updated_user is not None
        assert updated_user.email == "new@example.com"
        assert updated_user.username == created_user.username  # Unchanged
        
        # Verify in database
        retrieved_user = await get_user(db_session, created_user.id)
        assert retrieved_user.email == "new@example.com"
    
    async def test_update_user_password(self, db_session):
        """Test updating a user's password."""
        # Create a user first
        user_data = UserCreate(
            username="passworduser",
            email="password@example.com",
            password="oldpassword"
        )
        created_user = await create_user(db_session, user_data)
        old_hash = created_user.hashed_password
        
        # Update the user's password
        update_data = UserUpdate(password="newpassword")
        updated_user = await update_user(db_session, created_user.id, update_data)
        
        # Verify the password was re-hashed
        assert updated_user is not None
        assert updated_user.hashed_password != old_hash
        assert verify_password("newpassword", updated_user.hashed_password)
        assert not verify_password("oldpassword", updated_user.hashed_password)
    
    async def test_update_user_multiple_fields(self, db_session):
        """Test updating multiple fields at once."""
        # Create a user first
        user_data = UserCreate(
            username="multiuser",
            email="multi@example.com",
            password="password123"
        )
        created_user = await create_user(db_session, user_data)
        
        # Update multiple fields
        update_data = UserUpdate(
            email="newmulti@example.com",
            phone_number="+9876543210",
            is_active=False,
            is_admin=True
        )
        updated_user = await update_user(db_session, created_user.id, update_data)
        
        # Verify all updates
        assert updated_user.email == "newmulti@example.com"
        assert updated_user.phone_number == "+9876543210"
        assert updated_user.is_active is False
        assert updated_user.is_admin is True
    
    async def test_update_user_not_found(self, db_session):
        """Test updating a non-existent user."""
        update_data = UserUpdate(email="new@example.com")
        updated_user = await update_user(db_session, 999, update_data)
        assert updated_user is None


class TestDeleteUser:
    """Test user deletion functionality."""
    
    async def test_delete_user_success(self, db_session):
        """Test successfully deleting a user."""
        # Create a user first
        user_data = UserCreate(
            username="deleteuser",
            email="delete@example.com",
            password="password123"
        )
        created_user = await create_user(db_session, user_data)
        
        # Delete the user
        success = await delete_user(db_session, created_user.id)
        assert success is True
        
        # Verify the user is gone
        retrieved_user = await get_user(db_session, created_user.id)
        assert retrieved_user is None
    
    async def test_delete_user_not_found(self, db_session):
        """Test deleting a non-existent user."""
        success = await delete_user(db_session, 999)
        assert success is False


class TestUserUniqueness:
    """Test user uniqueness constraints."""
    
    async def test_create_user_duplicate_username(self, db_session):
        """Test that creating a user with duplicate username raises IntegrityError."""
        # Create first user
        user1_data = UserCreate(
            username="duplicateuser",
            email="user1@example.com",
            password="password123"
        )
        await create_user(db_session, user1_data)
        
        # Try to create second user with same username
        user2_data = UserCreate(
            username="duplicateuser",  # Same username
            email="user2@example.com",
            password="password456"
        )
        
        with pytest.raises(IntegrityError):
            await create_user(db_session, user2_data)
    
    async def test_create_user_duplicate_email(self, db_session):
        """Test that creating a user with duplicate email raises IntegrityError."""
        # Create first user
        user1_data = UserCreate(
            username="user1",
            email="duplicate@example.com",
            password="password123"
        )
        await create_user(db_session, user1_data)
        
        # Try to create second user with same email
        user2_data = UserCreate(
            username="user2",
            email="duplicate@example.com",  # Same email
            password="password456"
        )
        
        with pytest.raises(IntegrityError):
            await create_user(db_session, user2_data)
    
    async def test_update_user_duplicate_username(self, db_session):
        """Test that updating a user with duplicate username raises IntegrityError."""
        # Create two users
        user1_data = UserCreate(
            username="user1",
            email="user1@example.com",
            password="password123"
        )
        user2_data = UserCreate(
            username="user2",
            email="user2@example.com",
            password="password456"
        )
        
        user1 = await create_user(db_session, user1_data)
        await create_user(db_session, user2_data)
        
        # Try to update user1 to have user2's username
        update_data = UserUpdate(username="user2")
        
        with pytest.raises(IntegrityError):
            await update_user(db_session, user1.id, update_data)
    
    async def test_update_user_duplicate_email(self, db_session):
        """Test that updating a user with duplicate email raises IntegrityError."""
        # Create two users
        user1_data = UserCreate(
            username="user1",
            email="user1@example.com",
            password="password123"
        )
        user2_data = UserCreate(
            username="user2",
            email="user2@example.com",
            password="password456"
        )
        
        user1 = await create_user(db_session, user1_data)
        await create_user(db_session, user2_data)
        
        # Try to update user1 to have user2's email
        update_data = UserUpdate(email="user2@example.com")
        
        with pytest.raises(IntegrityError):
            await update_user(db_session, user1.id, update_data) 