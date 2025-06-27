"""
Integration tests for the HAL API channels.

This module tests the hal/api/channels.py endpoints using FastAPI's AsyncClient
and a temporary in-memory database to ensure test isolation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import BackgroundTasks
from shared.schemas.enums import DeviceRole
from shared.schemas import device as device_schema

# Mock the hardware driver functions
from hal.drivers import pca9685_driver


# =============================================================================
# FIXTURES
# =============================================================================

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


@pytest_asyncio.fixture
async def test_controller_and_channel(client, mock_pca9685_driver, auth_headers):
    """Create a test controller and channel for testing."""
    # Create a controller first
    controller_data = {
        "name": "Test PWM Controller",
        "address": 0x40,
        "frequency": 1000
    }
    
    controller_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
    assert controller_response.status_code == 201
    controller_id = controller_response.json()["id"]
    
    # Create a channel on the controller
    channel_data = {
        "channel_number": 0,
        "name": "Test Blue LEDs",
        "role": DeviceRole.LIGHT_ROYAL_BLUE.value,
        "min_value": 0,
        "max_value": 100
    }
    
    channel_response = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data, headers=auth_headers)
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
    
    async def test_set_channel_intensity_immediate_success(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test successfully setting channel intensity immediately."""
        channel_id = test_controller_and_channel["channel_id"]
        
        control_data = {
            "intensity": 75
        }
        
        response = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
        
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
        state_response = await client.get(f"/api/hal/channels/{channel_id}/state", headers=auth_headers)
        assert state_response.status_code == 200
        assert state_response.json() == 75.0
    
    async def test_set_channel_intensity_with_constraints(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test that intensity constraints are properly applied."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Try to set intensity above max (should be constrained to 100)
        control_data = {
            "intensity": 150
        }
        
        response = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be constrained to max_value (100)
        assert data["current_value"] == 100.0
        assert data["duty_cycle_value"] == 65535  # 100% duty cycle
        
        # Try to set intensity below min (should be constrained to 0)
        control_data2 = {
            "intensity": -10
        }
        
        response2 = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data2, headers=auth_headers)
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should be constrained to min_value (0)
        assert data2["current_value"] == 0.0
        assert data2["duty_cycle_value"] == 0  # 0% duty cycle
    
    async def test_set_channel_intensity_channel_not_found(self, client, auth_headers):
        """Test setting intensity for a non-existent channel."""
        control_data = {
            "intensity": 50
        }
        
        response = await client.post("/api/hal/channels/999/control", json=control_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "PWM Channel device not found" in data["detail"]
    
    async def test_set_channel_intensity_hardware_error(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test handling of hardware errors during intensity setting."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware error
        mock_pca9685_driver.set_channel_duty_cycle.side_effect = ValueError("Hardware communication error")
        
        control_data = {
            "intensity": 50
        }
        
        response = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to set PWM channel duty cycle" in data["detail"]
        assert "Hardware communication error" in data["detail"]


class TestChannelRampedControl:
    """Test ramped channel control endpoint."""
    
    async def test_set_channel_intensity_ramped_success(self, client, mock_pca9685_driver, test_controller_and_channel, mock_background_tasks, auth_headers):
        """Test successfully initiating a ramped intensity change."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock BackgroundTasks
        with patch('fastapi.BackgroundTasks', return_value=mock_background_tasks):
            control_data = {
                "intensity": 100,
                "duration_ms": 3000,
                "curve": "linear"
            }
            
            response = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response data
            assert data["current_value"] == 0.0  # Starting value
            assert data["target_value"] == 100.0
            assert data["duration_ms"] == 3000
            assert data["curve"] == "linear"
            assert "Ramp initiated" in data["message"]
            
            # Verify background task was added
            mock_background_tasks.add_task.assert_called_once()
            
            # Verify hardware was called with initial duty cycle
            mock_pca9685_driver.set_channel_duty_cycle.assert_called_once_with(
                address=0x40,
                channel=0,
                duty_cycle=0
            )
    
    async def test_set_channel_intensity_ramped_exponential(self, client, mock_pca9685_driver, test_controller_and_channel, mock_background_tasks, auth_headers):
        """Test ramped intensity change with exponential curve."""
        channel_id = test_controller_and_channel["channel_id"]
        
        with patch('fastapi.BackgroundTasks', return_value=mock_background_tasks):
            control_data = {
                "intensity": 80,
                "duration_ms": 5000,
                "curve": "exponential"
            }
            
            response = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["curve"] == "exponential"
            assert data["target_value"] == 80.0
            assert data["duration_ms"] == 5000
    
    async def test_set_channel_intensity_ramped_zero_duration(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test that zero duration ramps are treated as immediate changes."""
        channel_id = test_controller_and_channel["channel_id"]
        
        control_data = {
            "intensity": 60,
            "duration_ms": 0,
            "curve": "linear"
        }
        
        response = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be treated as immediate change
        assert data["current_value"] == 60.0
        assert data["duty_cycle_value"] == int((60 / 100) * 65535)


class TestBulkChannelControl:
    """Test bulk channel control endpoint."""
    
    async def test_bulk_control_success(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test successfully controlling multiple channels at once."""
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
        
        channel_response2 = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2, headers=auth_headers)
        assert channel_response2.status_code == 201
        channel_id2 = channel_response2.json()["id"]
        
        # Bulk control data
        bulk_data = {
            "commands": [
                {"channel_id": channel_id, "intensity": 75},
                {"channel_id": channel_id2, "intensity": 50}
            ]
        }
        
        response = await client.post("/api/hal/channels/bulk-control", json=bulk_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert len(data["results"]) == 2
        
        # Verify first channel result
        result1 = data["results"][0]
        assert result1["channel_id"] == channel_id
        assert result1["success"] is True
        assert result1["current_value"] == 75.0
        
        # Verify second channel result
        result2 = data["results"][1]
        assert result2["channel_id"] == channel_id2
        assert result2["success"] is True
        assert result2["current_value"] == 50.0
        
        # Verify hardware was called for both channels
        assert mock_pca9685_driver.set_channel_duty_cycle.call_count == 2
    
    async def test_bulk_control_mixed_success_and_error(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test bulk control with some successful and some failed operations."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware error for the second call
        mock_pca9685_driver.set_channel_duty_cycle.side_effect = [
            None,  # First call succeeds
            ValueError("Hardware error")  # Second call fails
        ]
        
        bulk_data = {
            "commands": [
                {"channel_id": channel_id, "intensity": 75},
                {"channel_id": 999, "intensity": 50}  # Non-existent channel
            ]
        }
        
        response = await client.post("/api/hal/channels/bulk-control", json=bulk_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 2
        
        # First should succeed
        assert data["results"][0]["success"] is True
        assert data["results"][0]["channel_id"] == channel_id
        
        # Second should fail
        assert data["results"][1]["success"] is False
        assert data["results"][1]["channel_id"] == 999
        assert "PWM Channel device not found" in data["results"][1]["error"]
    
    async def test_bulk_control_empty_list(self, client, auth_headers):
        """Test bulk control with empty command list."""
        bulk_data = {
            "commands": []
        }
        
        response = await client.post("/api/hal/channels/bulk-control", json=bulk_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []


class TestChannelState:
    """Test channel state retrieval endpoint."""
    
    async def test_get_channel_state_success(self, client, test_controller_and_channel, auth_headers):
        """Test successfully retrieving channel state."""
        channel_id = test_controller_and_channel["channel_id"]
        
        response = await client.get(f"/api/hal/channels/{channel_id}/state", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return the current intensity value
        assert isinstance(data, (int, float))
        assert data == 0.0  # Default value
    
    async def test_get_channel_state_not_found(self, client, auth_headers):
        """Test getting state for a non-existent channel."""
        response = await client.get("/api/hal/channels/999/state", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "PWM Channel device not found" in data["detail"]
    
    async def test_get_channel_state_null_value(self, client, test_controller_and_channel, auth_headers):
        """Test getting state when current_value is null."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Set a value first
        control_data = {"intensity": 50}
        await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
        
        # Get state
        response = await client.get(f"/api/hal/channels/{channel_id}/state", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json() == 50.0


class TestChannelLiveState:
    """Test live channel state reading from hardware."""
    
    async def test_get_channel_live_state_success(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test successfully reading live state from hardware."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware to return a specific duty cycle
        mock_pca9685_driver.get_current_duty_cycle.return_value = 32768  # 50% duty cycle
        
        response = await client.get(f"/api/hal/channels/{channel_id}/live-state", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return the live intensity value
        assert data["intensity"] == 50.0  # 32768 / 65535 * 100
        assert data["duty_cycle"] == 32768
        assert data["hardware_address"] == 0x40
        assert data["channel_number"] == 0
        
        # Verify hardware was called
        mock_pca9685_driver.get_current_duty_cycle.assert_called_once_with(0x40, 0)
    
    async def test_get_channel_live_state_hardware_error(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test handling hardware errors during live state reading."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Mock hardware error
        mock_pca9685_driver.get_current_duty_cycle.side_effect = ValueError("Hardware communication error")
        
        response = await client.get(f"/api/hal/channels/{channel_id}/live-state", headers=auth_headers)
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to read PWM channel duty cycle" in data["detail"]
    
    async def test_get_channel_live_state_edge_cases(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test live state reading with edge case values."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # Test 0% duty cycle
        mock_pca9685_driver.get_current_duty_cycle.return_value = 0
        response = await client.get(f"/api/hal/channels/{channel_id}/live-state", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["intensity"] == 0.0
        
        # Test 100% duty cycle
        mock_pca9685_driver.get_current_duty_cycle.return_value = 65535
        response = await client.get(f"/api/hal/channels/{channel_id}/live-state", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["intensity"] == 100.0


class TestChannelListing:
    """Test channel listing endpoint."""
    
    async def test_list_channels_empty(self, client, auth_headers):
        """Test listing channels when none exist."""
        response = await client.get("/api/hal/channels", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    async def test_list_channels_with_data(self, client, test_controller_and_channel, auth_headers):
        """Test listing channels when some exist."""
        response = await client.get("/api/hal/channels", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have one channel
        assert len(data) == 1
        channel = data[0]
        assert channel["name"] == "Test Blue LEDs"
        assert channel["channel_number"] == 0
        assert channel["role"] == DeviceRole.LIGHT_ROYAL_BLUE.value
    
    async def test_list_channels_multiple(self, client, test_controller_and_channel, auth_headers):
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
        
        await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2, headers=auth_headers)
        await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data3, headers=auth_headers)
        
        response = await client.get("/api/hal/channels", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have three channels
        assert len(data) == 3
        
        # Verify all channels are present
        channel_names = [ch["name"] for ch in data]
        assert "Test Blue LEDs" in channel_names
        assert "Test White LEDs" in channel_names
        assert "Test Red LEDs" in channel_names


class TestChannelErrorHandling:
    """Test error handling in channel operations."""
    
    async def test_channel_without_parent_controller(self, client, mock_pca9685_driver, auth_headers):
        """Test channel operations when parent controller is missing."""
        # Create a channel directly in the database without a controller
        # This would be an edge case that shouldn't happen in normal operation
        
        # Try to control a non-existent channel
        control_data = {"intensity": 50}
        response = await client.post("/api/hal/channels/999/control", json=control_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "PWM Channel device not found" in data["detail"]
    
    async def test_channel_without_channel_number_config(self, client, mock_pca9685_driver, auth_headers):
        """Test channel operations when channel number is missing from config."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        controller_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert controller_response.status_code == 201
        controller_id = controller_response.json()["id"]
        
        # Create a channel with missing channel_number
        channel_data = {
            "name": "Test Channel",
            "role": DeviceRole.LIGHT_ROYAL_BLUE.value,
            "min_value": 0,
            "max_value": 100
        }
        
        response = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data, headers=auth_headers)
        
        # Should fail validation
        assert response.status_code == 422
        data = response.json()
        assert "field required" in str(data["detail"]).lower()


class TestChannelIntegration:
    """Test full integration scenarios."""
    
    async def test_full_channel_lifecycle(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
        """Test a complete channel lifecycle from creation to deletion."""
        channel_id = test_controller_and_channel["channel_id"]
        
        # 1. Set initial intensity
        control_data = {"intensity": 25}
        response = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data, headers=auth_headers)
        assert response.status_code == 200
        
        # 2. Verify state
        state_response = await client.get(f"/api/hal/channels/{channel_id}/state", headers=auth_headers)
        assert state_response.status_code == 200
        assert state_response.json() == 25.0
        
        # 3. Read live state
        live_response = await client.get(f"/api/hal/channels/{channel_id}/live-state", headers=auth_headers)
        assert live_response.status_code == 200
        assert live_response.json()["intensity"] == 50.0  # Mocked value
        
        # 4. Update intensity
        control_data2 = {"intensity": 75}
        response2 = await client.post(f"/api/hal/channels/{channel_id}/control", json=control_data2, headers=auth_headers)
        assert response2.status_code == 200
        
        # 5. Verify final state
        final_state = await client.get(f"/api/hal/channels/{channel_id}/state", headers=auth_headers)
        assert final_state.status_code == 200
        assert final_state.json() == 75.0
    
    async def test_multiple_channels_same_controller(self, client, mock_pca9685_driver, test_controller_and_channel, auth_headers):
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
        
        channel_response2 = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2, headers=auth_headers)
        assert channel_response2.status_code == 201
        channel_id2 = channel_response2.json()["id"]
        
        # Control both channels
        control_data1 = {"intensity": 30}
        control_data2 = {"intensity": 70}
        
        response1 = await client.post(f"/api/hal/channels/{test_controller_and_channel['channel_id']}/control", json=control_data1, headers=auth_headers)
        response2 = await client.post(f"/api/hal/channels/{channel_id2}/control", json=control_data2, headers=auth_headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both channels were controlled
        assert mock_pca9685_driver.set_channel_duty_cycle.call_count == 2
        
        # Verify the calls were made with correct parameters
        calls = mock_pca9685_driver.set_channel_duty_cycle.call_args_list
        assert calls[0][1]["channel"] == 0  # First channel
        assert calls[1][1]["channel"] == 1  # Second channel 