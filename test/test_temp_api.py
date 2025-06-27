import pytest
from httpx import AsyncClient
from unittest.mock import Mock
from shared.core.config import settings

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio


async def test_discover_probes_with_user_token(client: AsyncClient, auth_headers: dict, mocker):
    """
    Tests that a normal user with a JWT token can access the endpoint.
    """
    mocker.patch('temp.api.probes.temperature_service.discover_sensors', return_value=['28-00000a1b2c3d'])
    response = await client.get("/probe/discover", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == ['28-00000a1b2c3d']


async def test_discover_probes_with_service_token(client: AsyncClient, mocker):
    """
    Tests that an internal service with the SERVICE_TOKEN can access the endpoint.
    """
    mocker.patch('temp.api.probes.temperature_service.discover_sensors', return_value=['28-00000a1b2c3d'])
    service_headers = {"Authorization": f"Bearer {settings.SERVICE_TOKEN}"}
    response = await client.get("/probe/discover", headers=service_headers)
    assert response.status_code == 200
    assert response.json() == ['28-00000a1b2c3d']


async def test_discover_probes_no_auth(client: AsyncClient, mocker):
    """
    Tests that a request with no authentication fails.
    """
    mocker.patch('temp.api.probes.temperature_service.discover_sensors', return_value=['28-00000a1b2c3d'])
    response = await client.get("/probe/discover")
    assert response.status_code == 401


async def test_check_1wire_endpoint(client: AsyncClient, mocker):
    """Test the 1-wire subsystem check endpoint."""
    # Mock the temperature_service.check_1wire_subsystem function
    mock_result = {
        "subsystem_available": True,
        "device_count": 2,
        "error": None,
        "details": None
    }
    mocker.patch('temp.api.probes.temperature_service.check_1wire_subsystem', return_value=mock_result)
    
    # Make request to check endpoint (no authentication required)
    response = await client.get("/probe/check")
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == mock_result


@pytest.mark.asyncio
async def test_get_current_reading_success(client: AsyncClient, auth_headers: dict, mocker):
    """Test successful current reading retrieval."""
    # Mock the temperature_service.get_current_reading function
    mock_temperature = 26.5
    mocker.patch('temp.api.probes.temperature_service.get_current_reading', return_value=mock_temperature)
    
    # Make authenticated request
    response = await client.get("/probe/28-00000a1b2c3d/current", headers=auth_headers)
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data == mock_temperature


@pytest.mark.asyncio
async def test_get_current_reading_not_found(client: AsyncClient, auth_headers: dict, mocker):
    """Test current reading when probe is not found."""
    # Mock the temperature_service.get_current_reading function to return None
    mocker.patch('temp.api.probes.temperature_service.get_current_reading', return_value=None)
    
    # Make authenticated request
    response = await client.get("/probe/28-00000deadbeef/current", headers=auth_headers)
    
    # Assert response
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_probe_device_lifecycle(client: AsyncClient, auth_headers: dict):
    """Test the complete lifecycle of a probe device registration."""
    
    # Step A: Create a new probe device
    create_data = {
        "name": "Test Probe",
        "device_type": "temperature_sensor",
        "address": "28-00000a1b2c3d",
        "role": "general",
        "poll_enabled": True,
        "poll_interval": 60,
        "unit": "C",
        "is_active": True
    }
    
    response = await client.post("/probe/", json=create_data, headers=auth_headers)
    assert response.status_code == 200
    created = response.json()
    device_id = created["id"]
    assert created["name"] == "Test Probe"
    assert created["device_type"] == "temperature_sensor"
    assert created["address"] == "28-00000a1b2c3d"
    
    # Step B: List all probe devices
    response = await client.get("/probe/list", headers=auth_headers)
    assert response.status_code == 200
    devices = response.json()
    assert any(d["id"] == device_id for d in devices)
    
    # Step C: Update the probe device
    update_data = {
        "name": "Updated Probe"
    }
    
    response = await client.patch(f"/probe/{device_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    updated_device = response.json()
    assert updated_device["name"] == "Updated Probe"
    assert updated_device["id"] == device_id
    
    # Step D: Delete the probe device
    response = await client.delete(f"/probe/{device_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Step E: Verify deletion
    response = await client.get("/probe/list", headers=auth_headers)
    assert response.status_code == 200
    devices = response.json()
    assert all(d["id"] != device_id for d in devices)


@pytest.mark.asyncio
async def test_create_probe_with_invalid_type(client: AsyncClient, auth_headers: dict):
    """Test creating a probe with invalid device type."""
    create_data = {
        "name": "Invalid Probe",
        "device_type": "wrong_type",  # Invalid type
        "address": "28-00000a1b2c3d",
        "role": "general",
        "poll_enabled": True,
        "poll_interval": 60,
        "unit": "C",
        "is_active": True
    }
    
    response = await client.post("/probe/", json=create_data, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert "must be 'temperature_sensor'" in data["detail"]


@pytest.mark.asyncio
async def test_create_probe_with_duplicate_address(client: AsyncClient, auth_headers: dict):
    """Test creating a probe with duplicate hardware ID."""
    # Create first probe
    create_data = {
        "name": "First Probe",
        "device_type": "temperature_sensor",
        "address": "28-00000a1b2c3d",
        "role": "general",
        "poll_enabled": True,
        "poll_interval": 60,
        "unit": "C",
        "is_active": True
    }
    
    response = await client.post("/probe/", json=create_data, headers=auth_headers)
    assert response.status_code == 200
    
    # Try to create second probe with same address
    create_data["name"] = "Second Probe"
    response = await client.post("/probe/", json=create_data, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_update_nonexistent_probe(client: AsyncClient, auth_headers: dict):
    """Test updating a probe that doesn't exist."""
    update_data = {
        "name": "Updated Name"
    }
    
    response = await client.patch("/probe/999", json=update_data, headers=auth_headers)
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


@pytest.mark.asyncio
async def test_delete_nonexistent_probe(client: AsyncClient, auth_headers: dict):
    """Test deleting a probe that doesn't exist."""
    response = await client.delete("/probe/999", headers=auth_headers)
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"] 