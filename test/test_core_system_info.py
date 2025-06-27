import pytest
from unittest.mock import Mock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_host_info(client: AsyncClient, auth_headers: dict, mocker):
    """Test the host info endpoint with mocked system data."""
    # Mock all the data-gathering functions
    mocker.patch('core.api.system_info.get_kernel_version', return_value='fake-kernel-1.0')
    mocker.patch('core.api.system_info.get_uptime', return_value='up 1 day, 2 hours, 30 minutes')
    mocker.patch('core.api.system_info.get_os_name', return_value='FakeOS')
    mocker.patch('core.api.system_info.get_release_name', return_value='FakeOS 2024.1')
    mocker.patch('core.api.system_info.get_hardware_model', return_value='TestModel-X1')

    # Make authenticated request
    response = await client.get("/api/host-info", headers=auth_headers)
    
    # Assert response
    assert response.status_code == 200
    
    data = response.json()
    assert data["kernel_version"] == "fake-kernel-1.0"
    assert data["uptime"] == "up 1 day, 2 hours, 30 minutes"
    assert data["os_name"] == "FakeOS"
    assert data["release_name"] == "FakeOS 2024.1"
    assert data["model"] == "TestModel-X1"


@pytest.mark.asyncio
async def test_get_system_usage(client: AsyncClient, auth_headers: dict, mocker):
    """Test the system usage endpoint with mocked psutil data."""
    # Mock psutil.cpu_percent
    mocker.patch('psutil.cpu_percent', return_value=15.7)
    
    # Mock psutil.virtual_memory
    mock_memory = Mock()
    mock_memory.total = 4 * 1024**3  # 4 GB
    mock_memory.used = 1 * 1024**3   # 1 GB
    mock_memory.percent = 25.0
    mocker.patch('psutil.virtual_memory', return_value=mock_memory)
    
    # Mock psutil.disk_usage
    mock_disk = Mock()
    mock_disk.total = 32 * 1024**3  # 32 GB
    mock_disk.used = 8 * 1024**3    # 8 GB
    mock_disk.percent = 25.0
    mocker.patch('psutil.disk_usage', return_value=mock_disk)

    # Make authenticated request
    response = await client.get("/api/system-usage", headers=auth_headers)
    
    # Assert response
    assert response.status_code == 200
    
    data = response.json()
    assert data["cpu_percent"] == 15.7
    assert data["memory_total_gb"] == 4.0
    assert data["memory_used_gb"] == 1.0
    assert data["memory_percent"] == 25.0
    assert data["disk_total_gb"] == 32.0
    assert data["disk_used_gb"] == 8.0
    assert data["disk_percent"] == 25.0


@pytest.mark.asyncio
async def test_get_host_info_unauthenticated(client: AsyncClient, mocker):
    """Test that host info endpoint requires authentication."""
    # Mock the functions to avoid actual system calls
    mocker.patch('core.api.system_info.get_kernel_version', return_value='fake-kernel-1.0')
    mocker.patch('core.api.system_info.get_uptime', return_value='up 1 day')
    mocker.patch('core.api.system_info.get_os_name', return_value='FakeOS')
    mocker.patch('core.api.system_info.get_release_name', return_value='FakeOS 2024.1')
    mocker.patch('core.api.system_info.get_hardware_model', return_value='TestModel-X1')

    # Make unauthenticated request
    response = await client.get("/api/host-info")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_system_usage_unauthenticated(client: AsyncClient, mocker):
    """Test that system usage endpoint requires authentication."""
    # Mock psutil functions
    mocker.patch('psutil.cpu_percent', return_value=10.0)
    mock_memory = Mock()
    mock_memory.total = 4 * 1024**3
    mock_memory.used = 1 * 1024**3
    mock_memory.percent = 25.0
    mocker.patch('psutil.virtual_memory', return_value=mock_memory)
    mock_disk = Mock()
    mock_disk.total = 32 * 1024**3
    mock_disk.used = 8 * 1024**3
    mock_disk.percent = 25.0
    mocker.patch('psutil.disk_usage', return_value=mock_disk)

    # Make unauthenticated request
    response = await client.get("/api/system-usage")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_host_info_error_handling(client: AsyncClient, auth_headers: dict, mocker):
    """Test host info endpoint error handling when system calls fail."""
    # Mock functions to raise exceptions
    mocker.patch('core.api.system_info.get_kernel_version', side_effect=Exception("Kernel error"))
    
    # Make authenticated request
    response = await client.get("/api/host-info", headers=auth_headers)
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    assert "Failed to retrieve host information" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_system_usage_error_handling(client: AsyncClient, auth_headers: dict, mocker):
    """Test system usage endpoint error handling when psutil calls fail."""
    # Mock psutil.cpu_percent to raise exception
    mocker.patch('psutil.cpu_percent', side_effect=Exception("CPU error"))
    
    # Make authenticated request
    response = await client.get("/api/system-usage", headers=auth_headers)
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    assert "Failed to retrieve system usage" in response.json()["detail"] 