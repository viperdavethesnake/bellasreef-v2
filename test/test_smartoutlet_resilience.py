"""
Test SmartOutlet Driver Resilience

This module tests the refactored SmartOutlet drivers to ensure they handle
connection errors gracefully by returning offline states instead of raising exceptions.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from smartoutlets.drivers.kasa import KasaDriver
from smartoutlets.drivers.shelly import ShellyDriver
from smartoutlets.drivers.vesync import VeSyncDriver
from smartoutlets.schemas import SmartOutletState
from smartoutlets.exceptions import OutletConnectionError, OutletTimeoutError


class TestSmartOutletResilience:
    """Test that SmartOutlet drivers handle connection errors gracefully."""
    
    @pytest.fixture
    def kasa_driver(self):
        """Create a Kasa driver instance for testing."""
        return KasaDriver("test_kasa", "192.168.1.100")
    
    @pytest.fixture
    def shelly_driver(self):
        """Create a Shelly driver instance for testing."""
        return ShellyDriver("test_shelly", "192.168.1.101")
    
    @pytest.fixture
    def vesync_driver(self):
        """Create a VeSync driver instance for testing."""
        auth_info = {
            "email": "test@example.com",
            "password": "password123",
            "time_zone": "America/New_York"
        }
        return VeSyncDriver("test_vesync", "192.168.1.102", auth_info)
    
    @pytest.mark.asyncio
    async def test_kasa_connection_error_returns_offline_state(self, kasa_driver):
        """Test that Kasa driver returns offline state on connection error."""
        # Mock the _create_smart_plug method to raise a connection error
        with patch.object(kasa_driver, '_create_smart_plug', side_effect=OutletConnectionError("Connection failed")):
            state = await kasa_driver.get_state()
            
            assert isinstance(state, SmartOutletState)
            assert state.is_on is False
            assert state.is_online is False
    
    @pytest.mark.asyncio
    async def test_kasa_timeout_error_returns_offline_state(self, kasa_driver):
        """Test that Kasa driver returns offline state on timeout error."""
        # Mock the _create_smart_plug method to raise a timeout error
        with patch.object(kasa_driver, '_create_smart_plug', side_effect=OutletTimeoutError("Operation timed out")):
            state = await kasa_driver.get_state()
            
            assert isinstance(state, SmartOutletState)
            assert state.is_on is False
            assert state.is_online is False
    
    @pytest.mark.asyncio
    async def test_kasa_successful_connection_returns_online_state(self, kasa_driver):
        """Test that Kasa driver returns online state on successful connection."""
        # Mock a successful SmartPlug instance
        mock_plug = MagicMock()
        mock_plug.is_on = True
        mock_plug.update = AsyncMock()
        mock_plug.emeter_realtime = {
            'power': 100.5,
            'voltage': 120.0,
            'current': 850  # mA
        }
        
        with patch.object(kasa_driver, '_create_smart_plug', return_value=mock_plug):
            state = await kasa_driver.get_state()
            
            assert isinstance(state, SmartOutletState)
            assert state.is_on is True
            assert state.is_online is True
            assert state.power_w == 100.5
            assert state.voltage_v == 120.0
            assert state.current_a == 0.85  # Converted from mA to A
    
    @pytest.mark.asyncio
    async def test_shelly_connection_error_returns_offline_state(self, shelly_driver):
        """Test that Shelly driver returns offline state on connection error."""
        # Mock the _get_device method to raise a connection error
        with patch.object(shelly_driver, '_get_device', side_effect=OutletConnectionError("Connection failed")):
            state = await shelly_driver.get_state()
            
            assert isinstance(state, SmartOutletState)
            assert state.is_on is False
            assert state.is_online is False
    
    @pytest.mark.asyncio
    async def test_shelly_successful_connection_returns_online_state(self, shelly_driver):
        """Test that Shelly driver returns online state on successful connection."""
        # Mock a successful device and relay
        mock_device = MagicMock()
        mock_device.gen = 2
        
        mock_relay = MagicMock()
        mock_relay.output = False
        mock_relay.apower = 50.0
        
        with patch.object(shelly_driver, '_get_device', return_value=mock_device):
            with patch.object(shelly_driver, '_get_relay', return_value=mock_relay):
                state = await shelly_driver.get_state()
                
                assert isinstance(state, SmartOutletState)
                assert state.is_on is False
                assert state.is_online is True
                assert state.power_w == 50.0
    
    @pytest.mark.asyncio
    async def test_vesync_connection_error_returns_offline_state(self, vesync_driver):
        """Test that VeSync driver returns offline state on connection error."""
        # Mock the _get_device method to raise a connection error
        with patch.object(vesync_driver, '_get_device', side_effect=OutletConnectionError("Connection failed")):
            state = await vesync_driver.get_state()
            
            assert isinstance(state, SmartOutletState)
            assert state.is_on is False
            assert state.is_online is False
    
    @pytest.mark.asyncio
    async def test_vesync_successful_connection_returns_online_state(self, vesync_driver):
        """Test that VeSync driver returns online state on successful connection."""
        # Mock a successful device
        mock_device = MagicMock()
        mock_device.is_on = True
        mock_device.update = MagicMock()
        mock_device.get_energy_usage.return_value = {
            'power': 75.2,
            'voltage': 119.8,
            'current': 0.63,
            'energy': 1.25
        }
        
        with patch.object(vesync_driver, '_get_device', return_value=mock_device):
            with patch('asyncio.get_running_loop') as mock_loop:
                mock_loop.return_value.run_in_executor = AsyncMock(side_effect=lambda executor, func: func())
                state = await vesync_driver.get_state()
                
                assert isinstance(state, SmartOutletState)
                assert state.is_on is True
                assert state.is_online is True
                assert state.power_w == 75.2
                assert state.voltage_v == 119.8
                assert state.current_a == 0.63
                assert state.energy_kwh == 1.25
    
    @pytest.mark.asyncio
    async def test_all_drivers_handle_authentication_errors(self, kasa_driver, shelly_driver, vesync_driver):
        """Test that all drivers handle authentication errors gracefully."""
        from smartoutlets.exceptions import OutletAuthenticationError
        
        # Test Kasa driver
        with patch.object(kasa_driver, '_create_smart_plug', side_effect=OutletAuthenticationError("Auth failed")):
            state = await kasa_driver.get_state()
            assert state.is_online is False
        
        # Test Shelly driver
        with patch.object(shelly_driver, '_get_device', side_effect=OutletAuthenticationError("Auth failed")):
            state = await shelly_driver.get_state()
            assert state.is_online is False
        
        # Test VeSync driver
        with patch.object(vesync_driver, '_get_device', side_effect=OutletAuthenticationError("Auth failed")):
            state = await vesync_driver.get_state()
            assert state.is_online is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 