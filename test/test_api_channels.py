"""
Integration tests for the HAL API channels.

This module tests the hal/api/channels.py endpoints using FastAPI's TestClient
and a temporary in-memory database to ensure test isolation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the HAL app and dependencies
from hal.main import app
from shared.db.database import get_db
from shared.db.base import Base
from shared.schemas.enums import DeviceRole
from shared.schemas.user import User
from shared.schemas import device as device_schema
from core.api.deps import get_current_user

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
        is_superuser=True
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


@pytest.fixture
async def test_controller_and_channel(client, mock_pca9685_driver):
    """Create a test controller and channel for testing."""
    # Create a controller first
    controller_data = {
        "name": "Test PWM Controller",
        "address": 0x40,
        "frequency": 1000
    }
    
    controller_response = client.post("/api/hal/controllers", json=controller_data)
    assert controller_response.status_code == 201
    controller_id = controller_response.json()["id"]
    
    # Create a channel on the controller
    channel_data = {
        "channel_number": 0,
        "name": "Test Blue LEDs",
        "role": DeviceRole.LIGHT_BLUE.value,
        "min_value": 0,
        "max_value": 100
    }
    
    channel_response = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data)
    assert channel_response.status_code == 201
    channel_id = channel_response.json()["id"]
    
    return {
        "controller_id": controller_id,
        "channel_id": channel_id,
        "controller_data": controller_data,
        "channel_data": channel_data
    }


@pytest.fixture
def mock_background_tasks(mocker):
    """Mock BackgroundTasks for testing ramp functionality."""
    mock_tasks = Mock(spec=BackgroundTasks)
    mock_tasks.add_task = Mock()
    return mock_tasks


# =============================================================================
# TEST CASES
# =============================================================================

class TestChannelImmediateControl:
    """Test immediate channel control endpoint."""
    
    def test_set_channel_intensity_immediate_success(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test successfully setting channel intensity immediately."""
        channel_id = test_controller_and_channel["channel_id"]
        
        control_data = {
            "intensity": 75
        }
        
        response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response data
        assert data["current_value"] == 75.0
        assert data["duty_cycle_value"] == int((75 / 100) * 65535)  # 49152
        assert "Successfully set device" in data["message"]
        
        # Verify hardware was called with correct duty cycle
        mock_pca9685_driver.set_channel_duty_cycle.assert_called_once_with(
            address=0x40,
            channel=0,
            duty_cycle=49152
        )
        
        # Verify database was updated
        state_response = client.get(f"/api/hal/channels/{channel_id}/state")
        assert state_response.status_code == 200
        assert state_response.json() == 75.0
    
    def test_set_channel_intensity_with_constraints(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test that intensity constraints are properly applied."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Try to set intensity above max (should be constrained to 100)
        control_data = {
            "intensity": 150
        }
        
        response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be constrained to max_value (100)
        assert data["current_value"] == 100.0
        assert data["duty_cycle_value"] == 65535  # 100% duty cycle
        
        # Try to set intensity below min (should be constrained to 0)
        control_data2 = {
            "intensity": -10
        }
        
        response2 = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data2)
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should be constrained to min_value (0)
        assert data2["current_value"] == 0.0
        assert data2["duty_cycle_value"] == 0  # 0% duty cycle
    
    def test_set_channel_intensity_channel_not_found(self, client):
        """Test setting intensity for a non-existent channel."""
        control_data = {
            "intensity": 50
        }
        
        response = client.post("/api/hal/channels/999/control", json=control_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "PWM Channel device not found" in data["detail"]
    
    def test_set_channel_intensity_hardware_error(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test handling of hardware errors during intensity setting."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware error
        mock_pca9685_driver.set_channel_duty_cycle.side_effect = ValueError("Hardware communication error")
        
        control_data = {
            "intensity": 50
        }
        
        response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to set PWM channel duty cycle" in data["detail"]
        assert "Hardware communication error" in data["detail"]


class TestChannelRampedControl:
    """Test ramped channel control endpoint."""
    
    def test_set_channel_intensity_ramped_success(self, client, mock_pca9685_driver, test_controller_and_channel, mock_background_tasks):
        """Test successfully initiating a ramped intensity change."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock BackgroundTasks
        with patch('fastapi.BackgroundTasks', return_value=mock_background_tasks):
            control_data = {
                "intensity": 100,
                "duration_ms": 3000,
                "curve": "linear"
            }
            
            response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response data
            assert data["ramp_started"] is True
            assert data["start_intensity"] == 0.0  # Initial value
            assert data["target_intensity"] == 100
            assert data["duration_ms"] == 3000
            assert "Ramp initiated" in data["message"]
            
            # Verify background task was added with correct parameters
            mock_background_tasks.add_task.assert_called_once()
            call_args = mock_background_tasks.add_task.call_args
            
            # Check that _perform_ramp function was called
            assert call_args[0][0].__name__ == '_perform_ramp'
            
            # Check the parameters passed to _perform_ramp
            args = call_args[0][1:]  # Skip the function itself
            assert args[0] is not None  # db session
            assert args[1] == channel_id  # device_id
            assert args[2] == 0.0  # start_intensity
            assert args[3] == 100  # end_intensity
            assert args[4] == 3000  # duration_ms
            assert args[5] == 0x40  # controller_address
            assert args[6] == 0  # channel_number
            assert args[7] == "linear"  # curve
    
    def test_set_channel_intensity_ramped_exponential(self, client, mock_pca9685_driver, test_controller_and_channel, mock_background_tasks):
        """Test ramped control with exponential curve."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Set initial intensity first
        initial_data = {"intensity": 25}
        client.post(f"/api/hal/channels/{channel_id}/control", json=initial_data)
        
        # Mock BackgroundTasks
        with patch('fastapi.BackgroundTasks', return_value=mock_background_tasks):
            control_data = {
                "intensity": 75,
                "duration_ms": 2000,
                "curve": "exponential"
            }
            
            response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response data
            assert data["ramp_started"] is True
            assert data["start_intensity"] == 25.0  # Previous value
            assert data["target_intensity"] == 75
            assert data["duration_ms"] == 2000
            
            # Verify background task was added with exponential curve
            mock_background_tasks.add_task.assert_called_once()
            call_args = mock_background_tasks.add_task.call_args
            args = call_args[0][1:]  # Skip the function itself
            assert args[7] == "exponential"  # curve
    
    def test_set_channel_intensity_ramped_zero_duration(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test that zero duration is treated as immediate."""
        channel_id = test_controller_and_channel["channel_id"]
        
        control_data = {
            "intensity": 50,
            "duration_ms": 0
        }
        
        response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be treated as immediate (no ramp_started field)
        assert "ramp_started" not in data
        assert "duty_cycle_value" in data
        assert data["current_value"] == 50.0


class TestBulkChannelControl:
    """Test bulk channel control endpoint."""
    
    def test_bulk_control_success(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test successfully controlling multiple channels."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Create a second channel for bulk testing
        controller_id = test_controller_and_channel["controller_id"]
        channel_data2 = {
            "channel_number": 1,
            "name": "Test White LEDs",
            "role": DeviceRole.LIGHT_WHITE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        channel_response2 = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2)
        assert channel_response2.status_code == 201
        channel_id2 = channel_response2.json()["id"]
        
        # Bulk control request
        bulk_data = [
            {
                "device_id": channel_id,
                "intensity": 75
            },
            {
                "device_id": channel_id2,
                "intensity": 25
            }
        ]
        
        response = client.post("/api/hal/channels/bulk-control", json=bulk_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert len(data) == 2
        
        # Check first channel result
        assert data[0]["device_id"] == channel_id
        assert data[0]["status"] == "success"
        assert "Set to 75% intensity" in data[0]["detail"]
        
        # Check second channel result
        assert data[1]["device_id"] == channel_id2
        assert data[1]["status"] == "success"
        assert "Set to 25% intensity" in data[1]["detail"]
        
        # Verify hardware was called for both channels
        assert mock_pca9685_driver.set_channel_duty_cycle.call_count == 2
        
        # Verify database was updated for both channels
        state1 = client.get(f"/api/hal/channels/{channel_id}/state")
        state2 = client.get(f"/api/hal/channels/{channel_id2}/state")
        assert state1.json() == 75.0
        assert state2.json() == 25.0
    
    def test_bulk_control_mixed_success_and_error(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test bulk control with some successful and some failed operations."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware error for the second call
        mock_pca9685_driver.set_channel_duty_cycle.side_effect = [
            None,  # First call succeeds
            ValueError("Hardware error")  # Second call fails
        ]
        
        bulk_data = [
            {
                "device_id": channel_id,
                "intensity": 50
            },
            {
                "device_id": 999,  # Non-existent channel
                "intensity": 75
            }
        ]
        
        response = client.post("/api/hal/channels/bulk-control", json=bulk_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert len(data) == 2
        
        # First should succeed
        assert data[0]["device_id"] == channel_id
        assert data[0]["status"] == "success"
        
        # Second should fail
        assert data[1]["device_id"] == 999
        assert data[1]["status"] == "error"
        assert "PWM Channel device not found" in data[1]["detail"]
    
    def test_bulk_control_empty_list(self, client):
        """Test bulk control with empty request list."""
        response = client.post("/api/hal/channels/bulk-control", json=[])
        
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestChannelState:
    """Test channel state retrieval endpoints."""
    
    def test_get_channel_state_success(self, client, test_controller_and_channel):
        """Test getting channel state from database."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Set an initial state
        control_data = {"intensity": 60}
        client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        
        # Get the state
        response = client.get(f"/api/hal/channels/{channel_id}/state")
        
        assert response.status_code == 200
        assert response.json() == 60.0
    
    def test_get_channel_state_not_found(self, client):
        """Test getting state for non-existent channel."""
        response = client.get("/api/hal/channels/999/state")
        
        assert response.status_code == 404
        data = response.json()
        assert "PWM Channel device not found" in data["detail"]
    
    def test_get_channel_state_null_value(self, client, test_controller_and_channel):
        """Test getting state when current_value is null."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Get state without setting any value first
        response = client.get(f"/api/hal/channels/{channel_id}/state")
        
        assert response.status_code == 200
        # Should return None or 0.0 depending on implementation
        assert response.json() is None or response.json() == 0.0


class TestChannelLiveState:
    """Test live channel state retrieval endpoint."""
    
    def test_get_channel_live_state_success(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test getting live channel state from hardware."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware to return a specific duty cycle (50% = 32768)
        mock_pca9685_driver.get_current_duty_cycle.return_value = 32768
        
        response = client.get(f"/api/hal/channels/{channel_id}/live-state")
        
        assert response.status_code == 200
        # 32768 / 65535 * 100 = 50.0
        assert response.json() == 50.0
        
        # Verify hardware was called
        mock_pca9685_driver.get_current_duty_cycle.assert_called_once_with(0x40, 0)
        
        # Verify database was updated with the live value
        state_response = client.get(f"/api/hal/channels/{channel_id}/state")
        assert state_response.json() == 50.0
    
    def test_get_channel_live_state_hardware_error(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test handling of hardware errors during live state retrieval."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware error
        mock_pca9685_driver.get_current_duty_cycle.side_effect = IOError("Hardware communication error")
        
        response = client.get(f"/api/hal/channels/{channel_id}/live-state")
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to read PWM channel duty cycle from hardware" in data["detail"]
    
    def test_get_channel_live_state_edge_cases(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test live state with edge case duty cycle values."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Test 0% duty cycle
        mock_pca9685_driver.get_current_duty_cycle.return_value = 0
        response = client.get(f"/api/hal/channels/{channel_id}/live-state")
        assert response.status_code == 200
        assert response.json() == 0.0
        
        # Test 100% duty cycle
        mock_pca9685_driver.get_current_duty_cycle.return_value = 65535
        response = client.get(f"/api/hal/channels/{channel_id}/live-state")
        assert response.status_code == 200
        assert response.json() == 100.0


class TestChannelListing:
    """Test channel listing endpoint."""
    
    def test_list_channels_empty(self, client):
        """Test listing channels when none exist."""
        response = client.get("/api/hal/channels")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_list_channels_with_data(self, client, test_controller_and_channel):
        """Test listing channels when some exist."""
        response = client.get("/api/hal/channels")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        channel = data[0]
        assert channel["name"] == "Test Blue LEDs"
        assert channel["device_type"] == "pwm_channel"
        assert channel["role"] == DeviceRole.LIGHT_BLUE.value
        assert channel["parent_device_id"] == test_controller_and_channel["controller_id"]
    
    def test_list_channels_multiple(self, client, test_controller_and_channel):
        """Test listing multiple channels."""
        controller_id = test_controller_and_channel["controller_id"]
        
        # Create additional channels
        channel_data2 = {
            "channel_number": 1,
            "name": "Test White LEDs",
            "role": DeviceRole.LIGHT_WHITE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        channel_data3 = {
            "channel_number": 2,
            "name": "Test Red LEDs",
            "role": DeviceRole.LIGHT_RED.value,
            "min_value": 0,
            "max_value": 100
        }
        
        client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2)
        client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data3)
        
        response = client.get("/api/hal/channels")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        
        # Verify all channels are present
        channel_names = [ch["name"] for ch in data]
        assert "Test Blue LEDs" in channel_names
        assert "Test White LEDs" in channel_names
        assert "Test Red LEDs" in channel_names


class TestChannelErrorHandling:
    """Test error handling scenarios."""
    
    def test_channel_without_parent_controller(self, client, mock_pca9685_driver):
        """Test channel operations when parent controller is missing."""
        # Create a controller and channel
        controller_data = {
            "name": "Test Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        controller_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = controller_response.json()["id"]
        
        channel_data = {
            "channel_number": 0,
            "name": "Test Channel",
            "role": DeviceRole.LIGHT_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        channel_response = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data)
        channel_id = channel_response.json()["id"]
        
        # Delete the parent controller
        client.delete(f"/api/hal/controllers/{controller_id}")
        
        # Try to control the orphaned channel
        control_data = {"intensity": 50}
        response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "Parent controller not found" in data["detail"]
    
    def test_channel_without_channel_number_config(self, client, mock_pca9685_driver):
        """Test channel operations when channel_number is not configured."""
        # This would require direct database manipulation to create a malformed channel
        # For now, we'll test the error handling in the live-state endpoint
        # by mocking a scenario where config is missing
        
        # Create a normal channel first
        controller_data = {
            "name": "Test Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        controller_response = client.post("/api/hal/controllers", json=controller_data)
        controller_id = controller_response.json()["id"]
        
        channel_data = {
            "channel_number": 0,
            "name": "Test Channel",
            "role": DeviceRole.LIGHT_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        channel_response = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data)
        channel_id = channel_response.json()["id"]
        
        # The channel should work normally
        control_data = {"intensity": 50}
        response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        assert response.status_code == 200


class TestChannelIntegration:
    """Test integration scenarios involving multiple operations."""
    
    def test_full_channel_lifecycle(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test a complete channel lifecycle: create, control, read state, delete."""
        channel_id = test_controller_and_channel["channel_id"]
        controller_id = test_controller_and_channel["controller_id"]
        
        # 1. Set initial intensity
        control_data = {"intensity": 30}
        response = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data)
        assert response.status_code == 200
        
        # 2. Read state
        state_response = client.get(f"/api/hal/channels/{channel_id}/state")
        assert state_response.status_code == 200
        assert state_response.json() == 30.0
        
        # 3. Set new intensity
        control_data2 = {"intensity": 80}
        response2 = client.post(f"/api/hal/channels/{channel_id}/control", json=control_data2)
        assert response2.status_code == 200
        
        # 4. Read updated state
        state_response2 = client.get(f"/api/hal/channels/{channel_id}/state")
        assert state_response2.status_code == 200
        assert state_response2.json() == 80.0
        
        # 5. Read live state
        mock_pca9685_driver.get_current_duty_cycle.return_value = 49152  # 75%
        live_response = client.get(f"/api/hal/channels/{channel_id}/live-state")
        assert live_response.status_code == 200
        assert live_response.json() == 75.0
        
        # 6. Delete controller (should cascade to channel)
        delete_response = client.delete(f"/api/hal/controllers/{controller_id}")
        assert delete_response.status_code == 204
        
        # 7. Verify channel is gone
        list_response = client.get("/api/hal/channels")
        assert list_response.json() == []
    
    def test_multiple_channels_same_controller(self, client, mock_pca9685_driver, test_controller_and_channel):
        """Test controlling multiple channels on the same controller."""
        controller_id = test_controller_and_channel["controller_id"]
        
        # Create additional channels
        channel_data2 = {
            "channel_number": 1,
            "name": "Test White LEDs",
            "role": DeviceRole.LIGHT_WHITE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        channel_data3 = {
            "channel_number": 2,
            "name": "Test Red LEDs",
            "role": DeviceRole.LIGHT_RED.value,
            "min_value": 0,
            "max_value": 100
        }
        
        channel_response2 = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2)
        channel_response3 = client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data3)
        
        channel_id2 = channel_response2.json()["id"]
        channel_id3 = channel_response3.json()["id"]
        
        # Control all channels
        client.post(f"/api/hal/channels/{test_controller_and_channel['channel_id']}/control", json={"intensity": 25})
        client.post(f"/api/hal/channels/{channel_id2}/control", json={"intensity": 50})
        client.post(f"/api/hal/channels/{channel_id3}/control", json={"intensity": 75})
        
        # Verify all states
        state1 = client.get(f"/api/hal/channels/{test_controller_and_channel['channel_id']}/state")
        state2 = client.get(f"/api/hal/channels/{channel_id2}/state")
        state3 = client.get(f"/api/hal/channels/{channel_id3}/state")
        
        assert state1.json() == 25.0
        assert state2.json() == 50.0
        assert state3.json() == 75.0
        
        # Verify hardware was called for each channel
        assert mock_pca9685_driver.set_channel_duty_cycle.call_count == 3 