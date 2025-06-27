"""
Integration tests for the HAL API controllers.

This module tests the hal/api/controllers.py endpoints using FastAPI's AsyncClient
and a temporary in-memory database to ensure test isolation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from shared.schemas.enums import DeviceRole


# =============================================================================
# TEST CASES
# =============================================================================

class TestControllerDiscovery:
    """Test the controller discovery endpoint."""
    
    @pytest.mark.asyncio
    async def test_discover_controllers_found(self, client, mock_pca9685_driver, auth_headers):
        """Test discovering controllers when devices are found."""
        # Mock check_board to return True for specific addresses
        mock_pca9685_driver.check_board.side_effect = lambda addr: addr in [0x40, 0x41]
        
        response = await client.get("/api/hal/controllers/discover", headers=auth_headers)
        
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
    
    @pytest.mark.asyncio
    async def test_discover_controllers_none_found(self, client, mock_pca9685_driver, auth_headers):
        """Test discovering controllers when no devices are found."""
        # Mock check_board to return False for all addresses
        mock_pca9685_driver.check_board.return_value = False
        
        response = await client.get("/api/hal/controllers/discover", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return one result indicating no devices found
        assert len(data) == 1
        assert data[0]["address"] == 0x40  # Default address
        assert data[0]["is_found"] is False
        assert "No PCA9685 controllers found" in data[0]["message"]


class TestControllerRegistration:
    """Test the controller registration endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_controller_success(self, client, mock_pca9685_driver, auth_headers):
        """Test successfully registering a new controller."""
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify the response data
        assert data["name"] == controller_data["name"]
        assert data["address"] == str(controller_data["address"])
        assert data["device_type"] == "pca9685"
        assert data["role"] == "controller"
        assert data["config"]["frequency"] == controller_data["frequency"]
        assert "id" in data
        
        # Verify the hardware check was called
        mock_pca9685_driver.check_board.assert_called_once_with(0x40)
    
    @pytest.mark.asyncio
    async def test_register_controller_device_not_found(self, client, mock_pca9685_driver, auth_headers):
        """Test registering a controller when the device is not found."""
        # Mock check_board to return False
        mock_pca9685_driver.check_board.return_value = False
        
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x41,
            "frequency": 1000
        }
        
        response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "No PCA9685 device found at address" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_controller_duplicate_address(self, client, mock_pca9685_driver, auth_headers):
        """Test registering a controller with an already registered address."""
        # First registration
        controller_data = {
            "name": "First PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        response1 = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Second registration with same address
        controller_data2 = {
            "name": "Second PWM Controller",
            "address": 0x40,
            "frequency": 1500
        }
        
        response2 = await client.post("/api/hal/controllers", json=controller_data2, headers=auth_headers)
        assert response2.status_code == 409
        data = response2.json()
        assert "already registered" in data["detail"]


class TestControllerListing:
    """Test the controller listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_controllers_empty(self, client, auth_headers):
        """Test listing controllers when none are registered."""
        response = await client.get("/api/hal/controllers", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    @pytest.mark.asyncio
    async def test_list_controllers_with_data(self, client, mock_pca9685_driver, auth_headers):
        """Test listing controllers when some are registered."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # List controllers
        response = await client.get("/api/hal/controllers", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have one controller
        assert len(data) == 1
        assert data[0]["name"] == controller_data["name"]
        assert data[0]["address"] == str(controller_data["address"])


class TestControllerDeletion:
    """Test the controller deletion endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_controller_success(self, client, mock_pca9685_driver, auth_headers):
        """Test successfully deleting a controller."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # Delete the controller
        response = await client.delete(f"/api/hal/controllers/{controller_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify it's gone
        list_response = await client.get("/api/hal/controllers", headers=auth_headers)
        assert list_response.status_code == 200
        assert list_response.json() == []
    
    @pytest.mark.asyncio
    async def test_delete_controller_not_found(self, client, auth_headers):
        """Test deleting a controller that doesn't exist."""
        response = await client.delete("/api/hal/controllers/999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "PCA9685 controller with ID 999 not found" in data["detail"]


class TestControllerFrequencyUpdate:
    """Test the controller frequency update endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_frequency_success(self, client, mock_pca9685_driver, auth_headers):
        """Test successfully updating a controller's frequency."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # Update frequency
        update_data = {"frequency": 2000}
        response = await client.patch(f"/api/hal/controllers/{controller_id}/frequency", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the response
        assert data["config"]["frequency"] == 2000
        
        # Verify the hardware was updated
        mock_pca9685_driver.set_frequency.assert_called_once_with(0x40, 2000)
    
    @pytest.mark.asyncio
    async def test_update_frequency_controller_not_found(self, client, auth_headers):
        """Test updating frequency for a controller that doesn't exist."""
        update_data = {"frequency": 2000}
        response = await client.patch("/api/hal/controllers/999/frequency", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "PCA9685 controller with ID 999 not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_update_frequency_hardware_error(self, client, mock_pca9685_driver, auth_headers):
        """Test updating frequency when hardware operation fails."""
        # Mock set_frequency to raise an exception
        mock_pca9685_driver.set_frequency.side_effect = Exception("Hardware error")
        
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # Update frequency
        update_data = {"frequency": 2000}
        response = await client.patch(f"/api/hal/controllers/{controller_id}/frequency", json=update_data, headers=auth_headers)
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to update PWM frequency on hardware" in data["detail"]


class TestChannelRegistration:
    """Test the channel registration endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_channel_success(self, client, mock_pca9685_driver, auth_headers):
        """Test successfully registering a new channel."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # Register a channel
        channel_data = {
            "name": "Test Channel",
            "channel_number": 0,
            "description": "Test PWM channel"
        }
        
        response = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify the response data
        assert data["name"] == channel_data["name"]
        assert data["channel_number"] == channel_data["channel_number"]
        assert data["description"] == channel_data["description"]
        assert data["device_id"] == controller_id
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_register_channel_controller_not_found(self, client, auth_headers):
        """Test registering a channel for a controller that doesn't exist."""
        channel_data = {
            "channel_number": 0,
            "name": "Test Channel",
            "role": "light_blue",
            "min_value": 0,
            "max_value": 100
        }
        
        response = await client.post("/api/hal/controllers/999/channels", json=channel_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "Parent controller with ID 999 not found or is not a PCA9685 controller" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_channel_duplicate_channel(self, client, mock_pca9685_driver, auth_headers):
        """Test registering a channel with a duplicate channel number."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # Register first channel
        channel_data = {
            "name": "First Channel",
            "channel_number": 0,
            "description": "First PWM channel"
        }
        
        response1 = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Register second channel with same number
        channel_data2 = {
            "name": "Second Channel",
            "channel_number": 0,
            "description": "Second PWM channel"
        }
        
        response2 = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data2, headers=auth_headers)
        assert response2.status_code == 409
        data = response2.json()
        assert "already registered" in data["detail"]


class TestChannelListing:
    """Test the channel listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_channels_empty(self, client, mock_pca9685_driver, auth_headers):
        """Test listing channels when none are registered."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # List channels
        response = await client.get(f"/api/hal/controllers/{controller_id}/channels", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    @pytest.mark.asyncio
    async def test_list_channels_with_data(self, client, mock_pca9685_driver, auth_headers):
        """Test listing channels when some are registered."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # Register a channel
        channel_data = {
            "name": "Test Channel",
            "channel_number": 0,
            "description": "Test PWM channel"
        }
        
        create_channel_response = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data, headers=auth_headers)
        assert create_channel_response.status_code == 201
        
        # List channels
        response = await client.get(f"/api/hal/controllers/{controller_id}/channels", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have one channel
        assert len(data) == 1
        assert data[0]["name"] == channel_data["name"]
        assert data[0]["channel_number"] == channel_data["channel_number"]
    
    @pytest.mark.asyncio
    async def test_list_channels_controller_not_found(self, client, auth_headers):
        """Test listing channels for a controller that doesn't exist."""
        response = await client.get("/api/hal/controllers/999/channels", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "Parent controller with ID 999 not found or is not a PCA9685 controller" in data["detail"]


class TestCascadingDeletion:
    """Test cascading deletion behavior."""
    
    @pytest.mark.asyncio
    async def test_delete_controller_deletes_channels(self, client, mock_pca9685_driver, auth_headers):
        """Test that deleting a controller also deletes its channels."""
        # Create a controller first
        controller_data = {
            "name": "Test PWM Controller",
            "address": 0x40,
            "frequency": 1000
        }
        
        create_response = await client.post("/api/hal/controllers", json=controller_data, headers=auth_headers)
        assert create_response.status_code == 201
        controller_id = create_response.json()["id"]
        
        # Register a channel
        channel_data = {
            "name": "Test Channel",
            "channel_number": 0,
            "description": "Test PWM channel"
        }
        
        create_channel_response = await client.post(f"/api/hal/controllers/{controller_id}/channels", json=channel_data, headers=auth_headers)
        assert create_channel_response.status_code == 201
        
        # Verify channel exists
        list_channels_response = await client.get(f"/api/hal/controllers/{controller_id}/channels", headers=auth_headers)
        assert list_channels_response.status_code == 200
        assert len(list_channels_response.json()) == 1
        
        # Delete the controller
        delete_response = await client.delete(f"/api/hal/controllers/{controller_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # Verify controller is gone
        list_controllers_response = await client.get("/api/hal/controllers", headers=auth_headers)
        assert list_controllers_response.status_code == 200
        assert list_controllers_response.json() == [] 