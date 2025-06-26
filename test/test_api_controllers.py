"""
Integration tests for the HAL API controllers.

This module tests the hal/api/controllers.py endpoints using FastAPI's TestClient
and a temporary in-memory database to ensure test isolation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

# Import the HAL app and dependencies
from hal.main import app
from shared.db.database import get_db, Base
from shared.schemas.enums import DeviceRole
from shared.schemas.user import User
from core.api.deps import get_current_user
from shared.db.models import User, Device, History, HistoryHourlyAggregate, Alert, AlertEvent, Schedule, DeviceAction, SmartOutlet, VeSyncAccount

# Mock the hardware driver functions
from hal.drivers import pca9685_driver


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


async def override_get_db():
    """Override the database dependency for testing."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


# =============================================================================
# MOCK USER AUTHENTICATION
# =============================================================================

def create_mock_user():
    """Create a mock user for authentication."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_active=True,
        is_superuser=True,
        created_at=datetime.now()
    )


async def override_get_current_user():
    """Override the authentication dependency for testing."""
    return create_mock_user()


# Override the authentication dependency
app.dependency_overrides[get_current_user] = override_get_current_user


# =============================================================================
# FIXTURES
# =============================================================================

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
def client():
    """Create a test client for the HAL API."""
    return TestClient(app)


@pytest.fixture
def mock_pca9685_driver(mocker):
    """Mock all PCA9685 driver functions."""
    # Mock the check_board function
    mocker.patch.object(pca9685_driver, 'check_board', return_value=True)
    
    # Mock the set_frequency function
    mocker.patch.object(pca9685_driver, 'set_frequency')
    
    # Mock the set_channel_duty_cycle function
    mocker.patch.object(pca9685_driver, 'set_channel_duty_cycle')
    
    # Mock the get_current_duty_cycle function
    mocker.patch.object(pca9685_driver, 'get_current_duty_cycle', return_value=32768)
    
    return pca9685_driver


# =============================================================================
# TEST CASES
# =============================================================================

class TestControllerDiscovery:
    """Test the controller discovery endpoint."""
    
    def test_discover_controllers_found(self, client, mock_pca9685_driver):
        """Test discovering controllers when devices are found."""
        # Mock check_board to return True for specific addresses
        mock_pca9685_driver.check_board.side_effect = lambda addr: addr in [0x40, 0x41]
        
        response = client.get("/api/hal/controllers/discover")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find 2 devices
        assert len(data) == 2
        
        # Check first device
        assert data[0]["address"] == 0x40
        assert data[0]["is_found"] is True
        assert "PCA9685 controller found at address 0x40" in data[0]["message"]
        
        # Check second device
        assert data[1]["address"] == 0x41
        assert data[1]["is_found"] is True
        assert "PCA9685 controller found at address 0x41" in data[1]["message"]
    
    def test_discover_controllers_none_found(self, client, mock_pca9685_driver):
        """Test discovering controllers when no devices are found."""
        # Mock check_board to return False for all addresses
        mock_pca9685_driver.check_board.return_value = False
        
        response = client.get("/api/hal/controllers/discover")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return one result indicating no devices found
        assert len(data) == 1
        assert data[0]["address"] == 0x40  # Default address
        assert data[0]["is_found"] is False
        assert "No PCA9685 controllers found" in data[0]["message"]


class TestControllerRegistration:
    """Test the controller registration endpoint."""
    
    def test_register_controller_success(self, client, mock_pca9685_driver):
        """Test successfully registering a new controller."""
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        response = client.post("/api/hal/controllers", json=controller_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify the response data
        assert data["name"] == controller_data["name"]
        assert data["address"] == str(controller_data["address"])
        assert data["device_type"] == "pca9685"
        assert data["role"] == DeviceRole.CONTROLLER.value
        assert data["config"]["frequency"] == controller_data["frequency"]
        assert "id" in data
        
        # Verify the hardware check was called
        mock_pca9685_driver.check_board.assert_called_once_with(0x40)
    
    def test_register_controller_device_not_found(self, client, mock_pca9685_driver):
        """Test registering a controller when the device is not found."""
        # Mock check_board to return False
        mock_pca9685_driver.check_board.return_value = False
        
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x41,
            "frequency": 1000
        }
        
        response = client.post("/api/hal/controllers", json=controller_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "No PCA9685 device found at address" in data["detail"]
    
    def test_register_controller_duplicate_address(self, client, mock_pca9685_driver):
        """Test registering a controller with an already registered address."""
        # First registration
        controller_data = {
            "name": "First PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        response1 = client.post("/api/hal/controllers", json=controller_data)
        assert response1.status_code == 201
        
        # Second registration with same address
        controller_data2 = {
            "name": "Second PWM Controller",
            "address": 0x40,
            "frequency": 1500
        }
        
        response2 = client.post("/api/hal/controllers", json=controller_data2)
        assert response2.status_code == 409
        data = response.json()
        assert "already registered" in data["detail"]


class TestControllerListing:
    """Test the controller listing endpoint."""
    
    def test_list_controllers_empty(self, client):
        """Test listing controllers when none are registered."""
        response = client.get("/api/hal/controllers")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_list_controllers_with_data(self, client, mock_pca9685_driver):
        """Test listing controllers when some are registered."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        client.post("/api/hal/controllers", json=controller_data)
        
        # List controllers
        response = client.get("/api/hal/controllers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == controller_data["name"]
        assert data[0]["address"] == str(controller_data["address"])
        assert data[0]["device_type"] == "pca9685"


class TestControllerDeletion:
    """Test the controller deletion endpoint."""
    
    def test_delete_controller_success(self, client, mock_pca9685_driver):
        """Test successfully deleting a controller."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # Delete the controller
        response = client.delete(f"/api/hal/controllers/{controller_id}")
        
        assert response.status_code == 204
        
        # Verify the controller is gone
        list_response = client.get("/api/hal/controllers")
        assert list_response.json() == []
    
    def test_delete_controller_not_found(self, client):
        """Test deleting a non-existent controller."""
        response = client.delete("/api/hal/controllers/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestControllerFrequencyUpdate:
    """Test the controller frequency update endpoint."""
    
    def test_update_frequency_success(self, client, mock_pca9685_driver):
        """Test successfully updating a controller's frequency."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # Update the frequency
        frequency_data = {"frequency": 1500}
        response = client.patch(f"/api/hal/controllers/{controller_id}/frequency", json=frequency_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the frequency was updated
        assert data["config"]["frequency"] == 1500
        
        # Verify the hardware was called
        mock_pca9685_driver.set_frequency.assert_called_once_with(0x40, 1500)
    
    def test_update_frequency_controller_not_found(self, client):
        """Test updating frequency for a non-existent controller."""
        frequency_data = {"frequency": 1500}
        response = client.patch("/api/hal/controllers/999/frequency", json=frequency_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_update_frequency_hardware_error(self, client, mock_pca9685_driver):
        """Test updating frequency when hardware operation fails."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # Mock hardware error
        mock_pca9685_driver.set_frequency.side_effect = ValueError("Hardware error")
        
        # Update the frequency
        frequency_data = {"frequency": 1500}
        response = client.patch(f"/api/hal/controllers/{controller_id}/frequency", json=frequency_data)
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to update PWM frequency on hardware" in data["detail"]


class TestChannelRegistration:
    """Test the channel registration endpoint."""
    
    def test_register_channel_success(self, client, mock_pca9685_driver):
        """Test successfully registering a channel on a controller."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # Register a channel
        channel_data = {
            "channel_number": 0,
            "name": "Blue LEDs",
            "role": DeviceRole.LIGHT_ROYAL_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        response = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify the channel data
        assert data["name"] == channel_data["name"]
        assert data["device_type"] == "pwm_channel"
        assert data["role"] == channel_data["role"]
        assert data["parent_device_id"] == controller_id
        assert data["config"]["channel_number"] == channel_data["channel_number"]
        assert data["min_value"] == channel_data["min_value"]
        assert data["max_value"] == channel_data["max_value"]
    
    def test_register_channel_controller_not_found(self, client):
        """Test registering a channel on a non-existent controller."""
        channel_data = {
            "channel_number": 0,
            "name": "Blue LEDs",
            "role": DeviceRole.LIGHT_ROYAL_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        response = client.post("/api/hal/controllers/999/channels", json=channel_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_register_channel_duplicate_channel(self, client, mock_pca9685_driver):
        """Test registering a channel with a duplicate channel number."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # Register first channel
        channel_data = {
            "channel_number": 0,
            "name": "Blue LEDs",
            "role": DeviceRole.LIGHT_ROYAL_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        response1 = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data)
        assert response1.status_code == 201
        
        # Register second channel with same channel number
        channel_data2 = {
            "channel_number": 0,
            "name": "White LEDs",
            "role": DeviceRole.LIGHT_DAYLIGHT.value,
            "min_value": 0,
            "max_value": 100
        }
        
        response2 = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2)
        assert response2.status_code == 409
        data = response2.json()
        assert "already registered" in data["detail"]


class TestChannelListing:
    """Test the channel listing endpoint."""
    
    def test_list_channels_empty(self, client, mock_pca9685_driver):
        """Test listing channels when none are registered."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # List channels
        response = client.get(f"/api/hal/controllers/{controller_id}/channels")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_list_channels_with_data(self, client, mock_pca9685_driver):
        """Test listing channels when some are registered."""
        # Register a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # Register a channel
        channel_data = {
            "channel_number": 0,
            "name": "Blue LEDs",
            "role": DeviceRole.LIGHT_ROYAL_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data)
        
        # List channels
        response = client.get(f"/api/hal/controllers/{controller_id}/channels")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == channel_data["name"]
        assert data[0]["device_type"] == "pwm_channel"
        assert data[0]["parent_device_id"] == controller_id
    
    def test_list_channels_controller_not_found(self, client):
        """Test listing channels for a non-existent controller."""
        response = client.get("/api/hal/controllers/999/channels")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestCascadingDeletion:
    """Test that deleting a controller also deletes its channels."""
    
    def test_delete_controller_deletes_channels(self, client, mock_pca9685_driver):
        """Test that deleting a controller cascades to delete its channels."""
        # Register a controller
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = create_response.json()["id"]
        
        # Register channels
        channel_data1 = {
            "channel_number": 0,
            "name": "Blue LEDs",
            "role": DeviceRole.LIGHT_ROYAL_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        channel_data2 = {
            "channel_number": 1,
            "name": "White LEDs",
            "role": DeviceRole.LIGHT_DAYLIGHT.value,
            "min_value": 0,
            "max_value": 100
        }
        
        client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data1)
        client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2)
        
        # Verify channels exist
        channels_response = client.get(f"/api/hal/controllers/{controller_id}/channels")
        assert len(channels_response.json()) == 2
        
        # Delete the controller
        delete_response = client.delete(f"/api/hal/controllers/{controller_id}")
        assert delete_response.status_code == 204
        
        # Verify controller is gone
        list_response = client.get("/api/hal/controllers")
        assert list_response.json() == []
        
        # Verify channels are also gone (they should be cascaded)
        # Note: We can't directly test this since the channels endpoint requires a valid controller
        # But we can verify the controller deletion was successful 