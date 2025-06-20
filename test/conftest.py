"""
Pytest configuration and common fixtures for Bella's Reef backend tests.

This file provides shared test fixtures, database setup, and configuration
for all test modules. It ensures consistent test environment across all
subsystem tests.

Usage:
    pytest backend/tests/ -v
    pytest backend/tests/test_system.py -v
    pytest backend/tests/test_scheduler.py -v --tb=short
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from shared.core.config import settings
from shared.db.database import Base, get_db

# Import the main app from core service
from core.main import app

# =============================================================================
# Test Configuration
# =============================================================================

# Use test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/bellasreef_test"

# Mock hardware settings for testing
MOCK_HARDWARE_CONFIG = {
    "PWM_PLATFORM": "noop",
    "PWM_FREQUENCY": 1000,
    "PWM_CHANNELS": 16,
    "PWM_I2C_ADDRESS": 0x40,
    "PWM_I2C_BUS": 1,
    "RASPBERRY_PI_PLATFORM": "noop",
    "GPIO_PLATFORM": "noop",
}

# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Create test engine with in-memory SQLite for faster tests
    # In production, use PostgreSQL test database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(test_session) -> AsyncGenerator[TestClient, None]:
    """Create test client with mocked database session."""
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_device():
    """Mock device for testing."""
    device = MagicMock()
    device.id = 1
    device.name = "Test Temperature Sensor"
    device.device_type = "temperature_sensor"
    device.address = "28-000000000000"
    device.poll_enabled = True
    device.poll_interval = 60
    device.unit = "C"
    device.is_active = True
    device.config = {"sensor_type": "DS18B20"}
    return device

@pytest.fixture
def mock_poll_result():
    """Mock poll result for testing."""
    from control.hardware.device_base import PollResult
    
    result = PollResult(
        success=True,
        value=25.5,
        json_value={"temperature": 25.5, "humidity": 60.0},
        metadata={"unit": "C", "sensor_id": "28-000000000000"},
        error=None
    )
    return result

@pytest.fixture
def mock_schedule():
    """Mock schedule for testing."""
    schedule = MagicMock()
    schedule.id = 1
    schedule.name = "Test Schedule"
    schedule.device_ids = [1, 2]
    schedule.schedule_type = "recurring"
    schedule.cron_expression = "0 8 * * *"  # Daily at 8 AM
    schedule.is_enabled = True
    schedule.action_type = "on"
    schedule.action_params = {"duration": 3600}
    return schedule

# =============================================================================
# Environment Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "DATABASE_URL": TEST_DATABASE_URL,
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "ADMIN_USERNAME": "testadmin",
        "ADMIN_PASSWORD": "testpass123",
        "ADMIN_EMAIL": "admin@test.com",
        **MOCK_HARDWARE_CONFIG
    }):
        yield

@pytest.fixture(autouse=True)
def mock_hardware():
    """Mock hardware dependencies for testing."""
    with patch("app.hardware.device_factory.DeviceFactory") as mock_factory, \
         patch("app.hardware.pwm.factory.PWMFactory") as mock_pwm_factory, \
         patch("lgpio") as mock_lgpio, \
         patch("adafruit_blinka") as mock_blinka:
        
        # Mock device factory
        mock_factory.create_device.return_value = AsyncMock()
        
        # Mock PWM factory
        mock_pwm_factory.create_pwm.return_value = AsyncMock()
        
        # Mock GPIO
        mock_lgpio.initialize.return_value = 0
        mock_lgpio.gpio_claim_output.return_value = 0
        
        yield {
            "device_factory": mock_factory,
            "pwm_factory": mock_pwm_factory,
            "lgpio": mock_lgpio,
            "blinka": mock_blinka
        }

# =============================================================================
# Test Utilities
# =============================================================================

def create_test_user_data(username: str = "testuser", email: str = "test@example.com") -> Dict[str, Any]:
    """Create test user data."""
    return {
        "username": username,
        "email": email,
        "password": "testpass123",
        "phone_number": "+1234567890"
    }

def create_test_device_data(
    name: str = "Test Device",
    device_type: str = "temperature_sensor",
    address: str = "test-address"
) -> Dict[str, Any]:
    """Create test device data."""
    return {
        "name": name,
        "device_type": device_type,
        "address": address,
        "poll_enabled": True,
        "poll_interval": 60,
        "unit": "C",
        "config": {"test": True}
    }

def create_test_schedule_data(
    name: str = "Test Schedule",
    schedule_type: str = "recurring"
) -> Dict[str, Any]:
    """Create test schedule data."""
    return {
        "name": name,
        "device_ids": [1, 2],
        "schedule_type": schedule_type,
        "cron_expression": "0 8 * * *",
        "action_type": "on",
        "action_params": {"duration": 3600}
    }

# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "system: mark test as system test"
    )
    config.addinivalue_line(
        "markers", "scheduler: mark test as scheduler test"
    )
    config.addinivalue_line(
        "markers", "poller: mark test as poller test"
    )
    config.addinivalue_line(
        "markers", "history: mark test as history test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )

def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names."""
    for item in items:
        if "test_system" in item.nodeid:
            item.add_marker(pytest.mark.system)
        elif "test_scheduler" in item.nodeid:
            item.add_marker(pytest.mark.scheduler)
        elif "test_poller" in item.nodeid:
            item.add_marker(pytest.mark.poller)
        elif "test_history" in item.nodeid:
            item.add_marker(pytest.mark.history) 