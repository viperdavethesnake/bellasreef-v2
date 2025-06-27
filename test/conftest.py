import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import the app instance from the HAL service being tested
from hal.main import app

# Import all models to ensure they are registered with the Base
from shared.db.models import Base, User, Device, Schedule, Alert
from shared.db.database import get_db
from shared.core.security import create_access_token
from datetime import timedelta

# --- Test Database Setup ---
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    This is the core fixture. It creates a clean database with all tables
    for every single test function, ensuring complete isolation.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an async test client that uses the clean db_session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    del app.dependency_overrides[get_db]

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Creates a fresh admin user for each test."""
    user = User(username="testuser", email="test@example.com", hashed_password="fakepassword", is_admin=True)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict[str, str]:
    """Generates fresh auth headers for the user created in each test."""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}

# --- Additional Test Utilities ---

@pytest_asyncio.fixture(scope="function")
async def mock_pca9685_driver(mocker):
    """
    Mock all PCA9685 driver functions for testing.
    This fixture provides consistent mocking across all tests.
    """
    from hal.drivers import pca9685_driver
    
    # Mock the check_board function
    mocker.patch.object(pca9685_driver, 'check_board', return_value=True)
    
    # Mock the set_frequency function
    mocker.patch.object(pca9685_driver, 'set_frequency')
    
    # Mock the set_channel_duty_cycle function
    mocker.patch.object(pca9685_driver, 'set_channel_duty_cycle')
    
    # Mock the get_current_duty_cycle function
    mocker.patch.object(pca9685_driver, 'get_current_duty_cycle', return_value=32768)
    
    return pca9685_driver

@pytest_asyncio.fixture(scope="function")
async def mock_background_tasks(mocker):
    """
    Mock FastAPI background tasks for testing.
    """
    mock_tasks = mocker.Mock()
    mocker.patch('fastapi.BackgroundTasks', return_value=mock_tasks)
    return mock_tasks 