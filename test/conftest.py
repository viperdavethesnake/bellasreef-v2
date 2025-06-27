import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Dict
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from temp.main import app
from shared.db.database import get_db
from shared.db.models import Base, User, Device, Schedule, Alert, History  # Add all models
from shared.core.security import create_access_token, get_password_hash
from shared.crud.user import create_user
from shared.schemas.user import UserCreate
from datetime import timedelta
from temp.deps import get_current_user_or_service
from fastapi import Request

# --- Test Database Setup ---
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean, isolated database session with a full schema for each test function.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, test_user: dict) -> AsyncGenerator[AsyncClient, None]:
    """Provides an async test client with intelligent dependency overrides."""
    def override_get_db():
        yield db_session
    async def override_get_user_or_service(request: Request):
        if "authorization" in request.headers:
            yield test_user["user"]
        else:
            yield None
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_or_service] = override_get_user_or_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    del app.dependency_overrides[get_db]
    del app.dependency_overrides[get_current_user_or_service]

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> dict:
    """Creates a fresh admin user in the clean database for each test."""
    # Define plaintext password for testing
    plain_password = "supersecret"
    
    # Create user with properly hashed password
    user = User(
        username="testadmin", 
        email="admin@example.com", 
        hashed_password=get_password_hash(plain_password), 
        is_admin=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Yield both user object and plaintext password
    yield {"user": user, "password": plain_password}

@pytest_asyncio.fixture
def auth_headers(test_user: dict) -> dict[str, str]:
    """Generates valid authentication headers for the test user."""
    token = create_access_token(data={"sub": test_user["user"].username})
    return {"Authorization": f"Bearer {token}"} 