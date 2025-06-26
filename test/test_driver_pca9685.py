"""
Unit tests for the PCA9685 hardware driver.

This module tests the hal/drivers/pca9685_driver.py functions using pytest and pytest-mock
to mock the hardware interactions and verify correct behavior.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

# Import the functions we're testing
from hal.drivers.pca9685_driver import (
    get_i2c_bus,
    check_board,
    set_channel_duty_cycle,
    set_frequency,
    get_current_duty_cycle
)


class TestGetI2CBus:
    """Test the I2C bus context manager."""
    
    @patch('hal.drivers.pca9685_driver.busio.I2C')
    @patch('hal.drivers.pca9685_driver.board.SCL')
    @patch('hal.drivers.pca9685_driver.board.SDA')
    def test_get_i2c_bus_creates_and_cleans_up_i2c(self, mock_sda, mock_scl, mock_i2c_class):
        """Test that get_i2c_bus creates I2C bus and properly cleans up."""
        mock_i2c = Mock()
        mock_i2c_class.return_value = mock_i2c
        
        with get_i2c_bus() as i2c:
            assert i2c == mock_i2c
            mock_i2c_class.assert_called_once_with(mock_scl, mock_sda)
        
        # Verify cleanup
        mock_i2c.deinit.assert_called_once()


class TestCheckBoard:
    """Test the check_board function."""
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_check_board_device_found(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test check_board when device is found at the address."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test
        result = check_board(0x40)
        
        # Assertions
        assert result is True
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x40)
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_check_board_device_not_found(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test check_board when device is not found (ValueError raised)."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = ValueError("Device not found")
        
        # Test
        result = check_board(0x41)
        
        # Assertions
        assert result is False
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x41)
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_check_board_other_exception(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test check_board when other exceptions occur."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = IOError("Communication error")
        
        # Test
        result = check_board(0x42)
        
        # Assertions
        assert result is False
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x42)


class TestSetFrequency:
    """Test the set_frequency function."""
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_set_frequency_success(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test set_frequency successfully sets the frequency."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test
        set_frequency(0x40, 1000)
        
        # Assertions
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x40)
        assert mock_pca9685.frequency == 1000
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_set_frequency_device_not_found(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test set_frequency when device is not found."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = ValueError("Device not found")
        
        # Test and assert exception
        with pytest.raises(ValueError, match="Device not found"):
            set_frequency(0x41, 1000)
        
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x41)
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_set_frequency_io_error(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test set_frequency when IO error occurs."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = IOError("Communication error")
        
        # Test and assert exception
        with pytest.raises(IOError, match="Communication error"):
            set_frequency(0x42, 1000)
        
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x42)


class TestSetChannelDutyCycle:
    """Test the set_channel_duty_cycle function."""
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_set_channel_duty_cycle_success(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test set_channel_duty_cycle successfully sets the duty cycle."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_channel = Mock()
        mock_pca9685.channels = [mock_channel] * 16  # 16 channels
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test
        set_channel_duty_cycle(0x40, 5, 32768)  # 50% duty cycle
        
        # Assertions
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x40)
        assert mock_pca9685.channels[5].duty_cycle == 32768
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_set_channel_duty_cycle_device_not_found(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test set_channel_duty_cycle when device is not found."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = ValueError("Device not found")
        
        # Test and assert exception
        with pytest.raises(ValueError, match="Device not found"):
            set_channel_duty_cycle(0x41, 0, 65535)
        
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x41)
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_set_channel_duty_cycle_io_error(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test set_channel_duty_cycle when IO error occurs."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = IOError("Communication error")
        
        # Test and assert exception
        with pytest.raises(IOError, match="Communication error"):
            set_channel_duty_cycle(0x42, 1, 0)
        
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x42)


class TestGetCurrentDutyCycle:
    """Test the get_current_duty_cycle function."""
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_get_current_duty_cycle_success(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test get_current_duty_cycle successfully reads the duty cycle."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_channel = Mock()
        mock_channel.duty_cycle = 49152  # 75% duty cycle
        mock_pca9685.channels = [mock_channel] * 16  # 16 channels
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test
        result = get_current_duty_cycle(0x40, 3)
        
        # Assertions
        assert result == 49152
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x40)
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_get_current_duty_cycle_device_not_found(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test get_current_duty_cycle when device is not found."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = ValueError("Device not found")
        
        # Test and assert exception
        with pytest.raises(ValueError, match="Device not found"):
            get_current_duty_cycle(0x41, 0)
        
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x41)
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_get_current_duty_cycle_io_error(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test get_current_duty_cycle when IO error occurs."""
        # Setup mocks
        mock_i2c = Mock()
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.side_effect = IOError("Communication error")
        
        # Test and assert exception
        with pytest.raises(IOError, match="Communication error"):
            get_current_duty_cycle(0x42, 1)
        
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x42)
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_get_current_duty_cycle_zero_value(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test get_current_duty_cycle returns zero duty cycle."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_channel = Mock()
        mock_channel.duty_cycle = 0  # 0% duty cycle
        mock_pca9685.channels = [mock_channel] * 16  # 16 channels
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test
        result = get_current_duty_cycle(0x40, 7)
        
        # Assertions
        assert result == 0
        mock_get_i2c_bus.assert_called_once()
        mock_pca9685_class.assert_called_once_with(mock_i2c, address=0x40)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_max_duty_cycle_values(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test setting and getting maximum duty cycle values."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_channel = Mock()
        mock_pca9685.channels = [mock_channel] * 16
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test maximum duty cycle (65535)
        set_channel_duty_cycle(0x40, 0, 65535)
        assert mock_pca9685.channels[0].duty_cycle == 65535
        
        # Test reading maximum duty cycle
        mock_channel.duty_cycle = 65535
        result = get_current_duty_cycle(0x40, 0)
        assert result == 65535
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_different_addresses(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test operations on different I2C addresses."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_channel = Mock()
        mock_pca9685.channels = [mock_channel] * 16
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test different addresses
        addresses = [0x40, 0x41, 0x42, 0x43]
        for addr in addresses:
            set_frequency(addr, 1000)
            mock_pca9685_class.assert_called_with(mock_i2c, address=addr)
            mock_pca9685_class.reset_mock()
    
    @patch('hal.drivers.pca9685_driver.get_i2c_bus')
    @patch('hal.drivers.pca9685_driver.PCA9685')
    def test_different_channels(self, mock_pca9685_class, mock_get_i2c_bus):
        """Test operations on different channel numbers."""
        # Setup mocks
        mock_i2c = Mock()
        mock_pca9685 = Mock()
        mock_channels = [Mock() for _ in range(16)]
        mock_pca9685.channels = mock_channels
        mock_get_i2c_bus.return_value.__enter__.return_value = mock_i2c
        mock_pca9685_class.return_value = mock_pca9685
        
        # Test different channels
        for channel in range(16):
            set_channel_duty_cycle(0x40, channel, 32768)
            assert mock_channels[channel].duty_cycle == 32768 