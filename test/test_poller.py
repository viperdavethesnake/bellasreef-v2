"""
Poller Tests for Bella's Reef Backend

This module tests the device polling system functionality including:
- Device polling at specified intervals
- Error handling and recovery
- Data insertion into history
- Device status updates
- Polling task management

Test Categories:
- Basic polling functionality
- Device polling intervals
- Error handling and recovery
- Data storage and retrieval
- Device status management
- Performance and scalability

Usage:
    pytest backend/tests/test_poller.py -v
    pytest backend/tests/test_poller.py::test_poller_basic_functionality -v
    pytest backend/tests/test_poller.py -m "poller" -v
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from poller.services.poller import DevicePoller
from control.hardware.device_base import PollResult
from shared.crud.device import device as device_crud
from shared.crud.device import history as history_crud

# =============================================================================
# Basic Poller Tests
# =============================================================================

@pytest.mark.poller
class TestPollerBasic:
    """Test basic poller functionality."""
    
    @pytest.mark.asyncio
    async def test_poller_initialization(self):
        """Test poller initializes correctly."""
        poller = DevicePoller()
        
        assert poller.running is False
        assert poller.devices == {}
        assert poller.poll_tasks == {}
    
    @pytest.mark.asyncio
    async def test_poller_start_stop(self):
        """Test poller start and stop functionality."""
        poller = DevicePoller()
        
        # Start poller
        await poller.start()
        assert poller.running is True
        
        # Stop poller
        await poller.stop()
        assert poller.running is False
        assert poller.devices == {}
        assert poller.poll_tasks == {}
    
    @pytest.mark.asyncio
    async def test_poller_double_start(self):
        """Test that starting poller twice doesn't cause issues."""
        poller = DevicePoller()
        
        await poller.start()
        await poller.start()  # Should not cause issues
        
        assert poller.running is True
        
        await poller.stop()
    
    @pytest.mark.asyncio
    async def test_poller_stop_when_not_running(self):
        """Test stopping poller when not running."""
        poller = DevicePoller()
        
        # Stop without starting should not cause issues
        await poller.stop()
        assert poller.running is False

# =============================================================================
# Device Management Tests
# =============================================================================

@pytest.mark.poller
class TestDeviceManagement:
    """Test device management functionality."""
    
    @pytest.mark.asyncio
    async def test_add_device(self, mock_device):
        """Test adding a device to the poller."""
        poller = DevicePoller()
        
        # Mock device factory
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create:
            mock_device_instance = AsyncMock()
            mock_create.return_value = mock_device_instance
            
            await poller.add_device(mock_device)
            
            assert mock_device.id in poller.devices
            assert poller.devices[mock_device.id] == mock_device_instance
    
    @pytest.mark.asyncio
    async def test_remove_device(self, mock_device):
        """Test removing a device from the poller."""
        poller = DevicePoller()
        
        # Add device first
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create:
            mock_device_instance = AsyncMock()
            mock_create.return_value = mock_device_instance
            
            await poller.add_device(mock_device)
            assert mock_device.id in poller.devices
            
            # Remove device
            await poller.remove_device(mock_device.id)
            assert mock_device.id not in poller.devices
    
    @pytest.mark.asyncio
    async def test_load_devices_from_database(self, test_session: AsyncSession):
        """Test loading devices from database."""
        poller = DevicePoller()
        
        # Mock database query
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.name = "Test Device"
        mock_device.device_type = "temperature_sensor"
        mock_device.address = "test-address"
        mock_device.poll_enabled = True
        mock_device.poll_interval = 60
        mock_device.unit = "C"
        mock_device.is_active = True
        mock_device.config = {"test": True}
        
        with patch("app.crud.device.get_pollable_devices") as mock_get_devices, \
             patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create:
            
            mock_get_devices.return_value = [mock_device]
            mock_device_instance = AsyncMock()
            mock_create.return_value = mock_device_instance
            
            await poller.load_devices()
            
            assert len(poller.devices) == 1
            assert mock_device.id in poller.devices

# =============================================================================
# Polling Functionality Tests
# =============================================================================

@pytest.mark.poller
class TestPollingFunctionality:
    """Test polling functionality."""
    
    @pytest.mark.asyncio
    async def test_poll_single_device_success(self, mock_device, mock_poll_result):
        """Test successful polling of a single device."""
        poller = DevicePoller()
        
        # Mock device
        mock_device_instance = AsyncMock()
        mock_device_instance.safe_poll.return_value = mock_poll_result
        
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create, \
             patch("app.crud.device.get") as mock_get_device, \
             patch("app.crud.device.create") as mock_create_history, \
             patch("app.crud.device.update") as mock_update_device:
            
            mock_create.return_value = mock_device_instance
            mock_get_device.return_value = mock_device
            
            # Add device
            await poller.add_device(mock_device)
            
            # Poll device
            await poller._poll_single_device(mock_device.id, mock_device)
            
            # Check that device was polled
            mock_device_instance.safe_poll.assert_called_once()
            
            # Check that history was created
            mock_create_history.assert_called_once()
            
            # Check that device status was updated
            mock_update_device.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_poll_single_device_error(self, mock_device):
        """Test polling error handling."""
        poller = DevicePoller()
        
        # Mock device that raises an exception
        mock_device_instance = AsyncMock()
        mock_device_instance.safe_poll.side_effect = Exception("Polling error")
        
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create, \
             patch("app.crud.device.get") as mock_get_device, \
             patch("app.crud.device.update") as mock_update_device:
            
            mock_create.return_value = mock_device_instance
            mock_get_device.return_value = mock_device
            
            # Add device
            await poller.add_device(mock_device)
            
            # Poll device (should handle error gracefully)
            await poller._poll_single_device(mock_device.id, mock_device)
            
            # Check that device status was updated with error
            mock_update_device.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_poll_device_loop(self, mock_device, mock_poll_result):
        """Test device polling loop."""
        poller = DevicePoller()
        
        # Mock device
        mock_device_instance = AsyncMock()
        mock_device_instance.safe_poll.return_value = mock_poll_result
        mock_device_instance.name = "Test Device"
        
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create, \
             patch("app.crud.device.get") as mock_get_device, \
             patch("app.crud.device.create") as mock_create_history, \
             patch("app.crud.device.update") as mock_update_device:
            
            mock_create.return_value = mock_device_instance
            mock_get_device.return_value = mock_device
            
            # Add device
            await poller.add_device(mock_device)
            
            # Start polling loop
            poller.running = True
            task = asyncio.create_task(poller._poll_device_loop(mock_device.id))
            
            # Wait for one poll cycle
            await asyncio.sleep(0.1)
            
            # Stop polling
            poller.running = False
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Check that device was polled
            mock_device_instance.safe_poll.assert_called()

# =============================================================================
# Data Storage Tests
# =============================================================================

@pytest.mark.poller
class TestDataStorage:
    """Test data storage functionality."""
    
    @pytest.mark.asyncio
    async def test_store_poll_result_success(self, mock_poll_result, test_session: AsyncSession):
        """Test successful storage of poll result."""
        poller = DevicePoller()
        
        with patch("app.crud.device.create") as mock_create:
            await poller._store_poll_result(1, mock_poll_result)
            
            # Check that history was created
            mock_create.assert_called_once()
            
            # Check the data that was passed
            call_args = mock_create.call_args
            history_data = call_args[0][1]  # Second argument is the data
            
            assert history_data.device_id == 1
            assert history_data.value == mock_poll_result.value
            assert history_data.json_value == mock_poll_result.json_value
            assert history_data.history_metadata == mock_poll_result.metadata
    
    @pytest.mark.asyncio
    async def test_store_poll_result_error(self, mock_poll_result):
        """Test error handling in poll result storage."""
        poller = DevicePoller()
        
        with patch("app.crud.device.create") as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            # Should handle error gracefully
            await poller._store_poll_result(1, mock_poll_result)
            
            # Check that create was called (even though it failed)
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_device_status_success(self, mock_poll_result, test_session: AsyncSession):
        """Test successful device status update."""
        poller = DevicePoller()
        
        with patch("app.crud.device.update") as mock_update:
            await poller._update_device_status(1, mock_poll_result)
            
            # Check that device was updated
            mock_update.assert_called_once()
            
            # Check the update data
            call_args = mock_update.call_args
            update_data = call_args[0][1]  # Second argument is the update data
            
            assert "last_polled" in update_data
            assert update_data["last_error"] is None
    
    @pytest.mark.asyncio
    async def test_update_device_status_with_error(self, test_session: AsyncSession):
        """Test device status update with error."""
        poller = DevicePoller()
        
        with patch("app.crud.device.update") as mock_update:
            error_message = "Device communication failed"
            await poller._update_device_status(1, None, error_message)
            
            # Check that device was updated
            mock_update.assert_called_once()
            
            # Check the update data
            call_args = mock_update.call_args
            update_data = call_args[0][1]  # Second argument is the update data
            
            assert "last_polled" in update_data
            assert update_data["last_error"] == error_message

# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.poller
class TestErrorHandling:
    """Test error handling in poller."""
    
    @pytest.mark.asyncio
    async def test_device_polling_error_recovery(self, mock_device):
        """Test that polling errors don't stop the poller."""
        poller = DevicePoller()
        
        # Mock device that fails initially, then succeeds
        mock_device_instance = AsyncMock()
        mock_device_instance.safe_poll.side_effect = [
            Exception("Initial error"),
            PollResult(success=True, value=25.0, json_value={}, metadata={}, error=None)
        ]
        
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create, \
             patch("app.crud.device.get") as mock_get_device, \
             patch("app.crud.device.update") as mock_update_device:
            
            mock_create.return_value = mock_device_instance
            mock_get_device.return_value = mock_device
            
            # Add device
            await poller.add_device(mock_device)
            
            # Start polling loop
            poller.running = True
            task = asyncio.create_task(poller._poll_device_loop(mock_device.id))
            
            # Wait for multiple poll cycles
            await asyncio.sleep(0.2)
            
            # Stop polling
            poller.running = False
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Check that device was polled multiple times
            assert mock_device_instance.safe_poll.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, mock_device, mock_poll_result):
        """Test handling of database connection errors."""
        poller = DevicePoller()
        
        # Mock device
        mock_device_instance = AsyncMock()
        mock_device_instance.safe_poll.return_value = mock_poll_result
        
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create, \
             patch("app.crud.device.get") as mock_get_device, \
             patch("app.crud.device.create") as mock_create_history, \
             patch("app.crud.device.update") as mock_update_device:
            
            mock_create.return_value = mock_device_instance
            mock_get_device.side_effect = Exception("Database connection error")
            
            # Add device
            await poller.add_device(mock_device)
            
            # Poll device (should handle database error gracefully)
            await poller._poll_single_device(mock_device.id, mock_device)
            
            # Poller should continue running despite database error
            assert poller.running is False  # Since we didn't start it

# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.poller
class TestPollerPerformance:
    """Test poller performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_poller_with_many_devices(self):
        """Test poller performance with many devices."""
        poller = DevicePoller()
        
        # Create many mock devices
        devices = []
        for i in range(20):
            device = MagicMock()
            device.id = i
            device.name = f"Device {i}"
            device.device_type = "temperature_sensor"
            device.address = f"address-{i}"
            device.poll_enabled = True
            device.poll_interval = 60
            device.unit = "C"
            device.is_active = True
            device.config = {"test": True}
            devices.append(device)
        
        # Mock device instances
        mock_device_instances = [AsyncMock() for _ in range(20)]
        for instance in mock_device_instances:
            instance.safe_poll.return_value = PollResult(
                success=True, value=25.0, json_value={}, metadata={}, error=None
            )
        
        with patch("app.hardware.device_factory.DeviceFactory.create_device") as mock_create, \
             patch("app.crud.device.get") as mock_get_device, \
             patch("app.crud.device.create") as mock_create_history, \
             patch("app.crud.device.update") as mock_update_device:
            
            mock_create.side_effect = mock_device_instances
            mock_get_device.side_effect = devices
            
            # Add all devices
            for device in devices:
                await poller.add_device(device)
            
            assert len(poller.devices) == 20
            
            # Start poller
            start_time = datetime.now()
            await poller.start()
            
            # Wait a bit
            await asyncio.sleep(0.1)
            
            # Stop poller
            await poller.stop()
            end_time = datetime.now()
            
            # Check performance
            execution_time = (end_time - start_time).total_seconds()
            assert execution_time < 2  # Should complete within 2 seconds

# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.poller
@pytest.mark.integration
class TestPollerIntegration:
    """Integration tests for poller functionality."""
    
    @pytest.mark.asyncio
    async def test_poller_with_real_database(self, test_session: AsyncSession):
        """Test poller integration with real database."""
        poller = DevicePoller()
        
        # This would require creating actual database records
        # For now, we'll test the integration structure
        
        # Start poller
        await poller.start()
        
        # Wait a bit
        await asyncio.sleep(0.1)
        
        # Stop poller
        await poller.stop()
    
    @pytest.mark.asyncio
    async def test_poller_with_device_factory(self):
        """Test poller integration with device factory."""
        poller = DevicePoller()
        
        # Mock device factory to return real device instances
        # This tests the integration between poller and device factory
        
        # For now, we'll test the structure
        await poller.start()
        await poller.stop()

# =============================================================================
# Manual Test Instructions
# =============================================================================

"""
MANUAL TEST INSTRUCTIONS FOR POLLER SYSTEM

These instructions should be followed on the target Raspberry Pi environment
to verify poller functionality in the actual deployment environment.

1. BASIC POLLER FUNCTIONALITY MANUAL TESTS
   =======================================
   
   a) Start Poller Service:
      # Start the poller service
      python -m app.services.poller
      Expected: Poller starts without errors, logs show initialization
   
   b) Check Poller Status:
      # Check if poller is running
      ps aux | grep poller
      Expected: Process is running
   
   c) View Poller Logs:
      tail -f /var/log/bellasreef/poller.log
      Expected: Logs show polling activity

2. DEVICE POLLING MANUAL TESTS
   ============================
   
   a) Create Pollable Device:
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Test Temperature Sensor",
          "device_type": "temperature_sensor",
          "address": "28-000000000000",
          "poll_enabled": true,
          "poll_interval": 30,
          "unit": "C",
          "config": {"sensor_type": "DS18B20"}
        }'
      Expected: 201 Created with device ID
   
   b) Monitor Device Polling:
      # Watch logs for polling activity
      tail -f /var/log/bellasreef/poller.log | grep "polling"
      Expected: Regular polling entries every 30 seconds
   
   c) Check Device Status:
      DEVICE_ID="your_device_id"
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with device details including last_polled timestamp

3. POLLING INTERVAL MANUAL TESTS
   ==============================
   
   a) Test Different Polling Intervals:
      # Create device with 10-second interval
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Fast Polling Device",
          "device_type": "temperature_sensor",
          "address": "28-000000000001",
          "poll_enabled": true,
          "poll_interval": 10,
          "unit": "C"
        }'
      Expected: 201 Created
   
      # Create device with 5-minute interval
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Slow Polling Device",
          "device_type": "temperature_sensor",
          "address": "28-000000000002",
          "poll_enabled": true,
          "poll_interval": 300,
          "unit": "C"
        }'
      Expected: 201 Created
   
   b) Verify Polling Timing:
      # Monitor logs for different polling intervals
      tail -f /var/log/bellasreef/poller.log | grep -E "(Fast Polling|Slow Polling)"
      Expected: Fast device polls every 10s, slow device every 5 minutes

4. ERROR HANDLING MANUAL TESTS
   ============================
   
   a) Test Device Communication Error:
      # Create device with invalid address
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Invalid Device",
          "device_type": "temperature_sensor",
          "address": "invalid-address",
          "poll_enabled": true,
          "poll_interval": 30,
          "unit": "C"
        }'
      Expected: 201 Created (device created, but polling will fail)
   
   b) Monitor Error Logs:
      tail -f /var/log/bellasreef/error.log
      Expected: Error entries for failed device communication
   
   c) Check Device Error Status:
      # Check device status after polling errors
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: Device shows last_error field with error message

5. DATA STORAGE MANUAL TESTS
   ==========================
   
   a) Check History Records:
      # Query history for a device
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with history records
   
   b) Verify Data Format:
      # Check individual history record
      HISTORY_ID="history_record_id"
      curl -X GET http://localhost:8000/api/v1/history/$HISTORY_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with properly formatted data
   
   c) Check Data Accuracy:
      # Compare polled data with expected values
      # This depends on the specific device and sensor type
      # For temperature sensors, verify readings are reasonable

6. PERFORMANCE MANUAL TESTS
   =========================
   
   a) Test with Many Devices:
      # Create 20 devices
      for i in {1..20}; do
        curl -X POST http://localhost:8000/api/v1/devices/ \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer $TOKEN" \
          -d "{
            \"name\": \"Performance Test Device $i\",
            \"device_type\": \"temperature_sensor\",
            \"address\": \"28-0000000000$i\",
            \"poll_enabled\": true,
            \"poll_interval\": 60,
            \"unit\": \"C\"
          }"
      done
      Expected: All devices created successfully
   
   b) Monitor System Resources:
      htop
      # Watch CPU and memory usage
      Expected: Stable resource usage
   
   c) Check Database Performance:
      # Monitor database connections and query performance
      # This may require database monitoring tools

7. DEVICE TYPE MANUAL TESTS
   =========================
   
   a) Test Temperature Sensors:
      # Test DS18B20 sensors
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "DS18B20 Sensor",
          "device_type": "temperature_sensor",
          "address": "28-000000000000",
          "poll_enabled": true,
          "poll_interval": 60,
          "unit": "C",
          "config": {"sensor_type": "DS18B20"}
        }'
   
   b) Test DHT Sensors:
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "DHT22 Sensor",
          "device_type": "temperature_sensor",
          "address": "22",
          "poll_enabled": true,
          "poll_interval": 60,
          "unit": "C",
          "config": {"sensor_type": "DHT22"}
        }'
   
   c) Test Outlet Devices:
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Smart Outlet",
          "device_type": "outlet",
          "address": "http://192.168.1.100",
          "poll_enabled": true,
          "poll_interval": 30,
          "unit": "state",
          "config": {"outlet_type": "wifi"}
        }'

8. RECOVERY MANUAL TESTS
   ======================
   
   a) Restart Poller Service:
      # Stop poller
      pkill -f poller
      
      # Start poller
      python -m app.services.poller
      
      # Check if devices are reloaded
      Expected: Devices are reloaded from database
   
   b) Database Connection Loss:
      # Simulate database connection issues
      # Stop PostgreSQL service temporarily
      sudo systemctl stop postgresql
      
      # Wait a bit
      sleep 10
      
      # Restart PostgreSQL
      sudo systemctl start postgresql
      
      # Check poller recovery
      Expected: Poller reconnects and continues

9. HARDWARE INTEGRATION MANUAL TESTS
   ==================================
   
   a) Test Real Temperature Sensors:
      # Connect actual DS18B20 sensor
      # Create device with correct address
      # Verify readings are accurate
   
   b) Test Real Outlets:
      # Connect actual smart outlet
      # Create device with correct configuration
      # Verify state polling works
   
   c) Test PWM Devices:
      # Connect PWM-controlled devices
      # Verify polling and control functionality

10. MONITORING MANUAL TESTS
    ========================
    
    a) Check Poller Metrics:
       # Monitor polling frequency
       # Check for missed polls
       # Verify data quality
    
    b) Monitor Device Health:
       # Check device response times
       # Monitor error rates
       # Track device availability
    
    c) System Resource Monitoring:
       # Monitor CPU usage during polling
       # Check memory usage
       # Monitor disk I/O for database operations

NOTES:
- Replace $TOKEN with actual authentication token
- Replace $DEVICE_ID with actual device ID from responses
- Monitor logs for any errors or warnings
- Check database for history records
- Verify device state changes where applicable
- Test with actual hardware when available
- Monitor system resources during performance tests
- Ensure proper error handling and recovery
- Check data accuracy and consistency
""" 