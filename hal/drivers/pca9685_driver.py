import board
import busio
import os
import threading
import time
from typing import Optional, Dict, Any
from adafruit_pca9685 import PCA9685
from shared.utils.logger import get_logger

logger = get_logger(__name__)

# Log the full path of the Adafruit PCA9685 library in use
try:
    import adafruit_pca9685
    logger.warning(f"ADAFRUIT_LIBRARY_PATH: {adafruit_pca9685.__file__}")
except Exception as e:
    logger.warning(f"ADAFRUIT_LIBRARY_PATH: Could not determine path: {e}")

class PCA9685ControllerManager:
    """
    Thread-safe singleton manager for PCA9685 controllers.
    Manages a single shared I2C bus instance and maintains PCA9685 objects indexed by address.
    Implements robust connection pooling and error recovery.
    """
    _instance: Optional['PCA9685ControllerManager'] = None
    _lock = threading.RLock()  # Reentrant lock for thread safety
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(PCA9685ControllerManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:  # Double-checked locking
                    self._i2c_bus: Optional[busio.I2C] = None
                    self._controllers: Dict[int, PCA9685] = {}
                    self._channel_cache: Dict[int, Dict[int, int]] = {}  # {address: {channel: last_duty_cycle}}
                    self._connection_errors: Dict[int, float] = {}  # {address: last_error_timestamp}
                    self._max_retry_interval = 30.0  # seconds
                    self._initialized = True
                    logger.info("PCA9685ControllerManager: Initialized singleton instance")

    def _get_i2c_bus(self) -> busio.I2C:
        """Get or create the I2C bus with error handling."""
        if self._i2c_bus is None:
            try:
                logger.info("PCA9685ControllerManager: Creating new I2C bus")
                self._i2c_bus = busio.I2C(board.SCL, board.SDA)
                logger.info("PCA9685ControllerManager: I2C bus created successfully")
            except Exception as e:
                logger.error(f"PCA9685ControllerManager: Failed to create I2C bus: {e}")
                raise
        return self._i2c_bus

    def _should_retry_connection(self, address: int) -> bool:
        """Check if enough time has passed to retry a failed connection."""
        if address not in self._connection_errors:
            return True
        time_since_error = time.time() - self._connection_errors[address]
        return time_since_error > self._max_retry_interval

    def _mark_connection_error(self, address: int):
        """Mark a connection error for an address."""
        self._connection_errors[address] = time.time()

    def get_controller(self, address: int) -> PCA9685:
        """
        Get or create a PCA9685 controller for the given address with error recovery.
        
        Args:
            address: The I2C address of the PCA9685 board.
            
        Returns:
            PCA9685 object for the given address.
            
        Raises:
            ValueError: If the device is not found and retry is not allowed.
            IOError: On persistent communication errors.
        """
        with self._lock:
            # Check if we should retry a previously failed connection
            if address in self._connection_errors and not self._should_retry_connection(address):
                time_until_retry = self._max_retry_interval - (time.time() - self._connection_errors[address])
                raise IOError(f"Connection to address 0x{address:02X} failed recently. Retry in {time_until_retry:.1f} seconds")
            
            # Return existing controller if available
            if address in self._controllers:
                logger.debug(f"PCA9685ControllerManager: Reusing existing controller at 0x{address:02X}")
                return self._controllers[address]
            
            # Create new controller
            try:
                logger.info(f"PCA9685ControllerManager: Creating new controller at 0x{address:02X}")
                i2c_bus = self._get_i2c_bus()
                controller = PCA9685(i2c_bus, address=address)
                controller.frequency = 1000  # Always set frequency immediately after instantiation
                self._controllers[address] = controller
                self._channel_cache[address] = {}
                
                # Clear any previous connection errors for this address
                if address in self._connection_errors:
                    del self._connection_errors[address]
                
                logger.info(f"PCA9685ControllerManager: Successfully created controller at 0x{address:02X}")
                return controller
                
            except Exception as e:
                self._mark_connection_error(address)
                logger.error(f"PCA9685ControllerManager: Failed to create controller at 0x{address:02X}: {e}")
                raise

    def remove_controller(self, address: int):
        """Remove a controller from the cache (useful for cleanup or reconnection)."""
        with self._lock:
            if address in self._controllers:
                logger.info(f"PCA9685ControllerManager: Removing controller at 0x{address:02X}")
                del self._controllers[address]
            if address in self._channel_cache:
                del self._channel_cache[address]
            if address in self._connection_errors:
                del self._connection_errors[address]

    def cleanup(self):
        """Clean up I2C bus and all controllers."""
        with self._lock:
            logger.info("PCA9685ControllerManager: Starting cleanup")
            if self._i2c_bus:
                try:
                    self._i2c_bus.deinit()
                    logger.info("PCA9685ControllerManager: I2C bus deinitialized")
                except Exception as e:
                    logger.error(f"PCA9685ControllerManager: Error deinitializing I2C bus: {e}")
                finally:
                    self._i2c_bus = None
            
            self._controllers.clear()
            self._channel_cache.clear()
            self._connection_errors.clear()
            logger.info("PCA9685ControllerManager: Cleanup completed")

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the manager for debugging."""
        with self._lock:
            return {
                "i2c_bus_active": self._i2c_bus is not None,
                "controllers_count": len(self._controllers),
                "cached_channels_count": sum(len(cache) for cache in self._channel_cache.values()),
                "connection_errors_count": len(self._connection_errors),
                "controller_addresses": list(self._controllers.keys()),
                "error_addresses": list(self._connection_errors.keys())
            }

# Global singleton instance
_manager_instance: Optional[PCA9685ControllerManager] = None

def get_manager() -> PCA9685ControllerManager:
    """Get the global singleton manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PCA9685ControllerManager()
    return _manager_instance

def cleanup_manager():
    """Clean up the global manager instance."""
    global _manager_instance
    if _manager_instance is not None:
        _manager_instance.cleanup()
        _manager_instance = None

def check_board(address: int) -> bool:
    """
    Checks if a PCA9685 board is present at the given I2C address.

    Args:
        address: The I2C address to check (e.g., 0x40).

    Returns:
        True if a device responds, False otherwise.
    """
    for attempt in range(2):  # Try once, retry once
        try:
            manager = get_manager()
            manager.get_controller(address)
            return True
        except ValueError:
            # This typically means the device was not found.
            if attempt == 0:
                logger.error(f"Hardware error in check_board: controller={address}, function=check_board, error=ValueError (device not found)")
            return False
        except Exception as e:
            # Catch any other unexpected errors during I2C communication.
            if attempt == 0:
                logger.error(f"Hardware error in check_board: controller={address}, function=check_board, error={type(e).__name__}: {e}")
            elif attempt == 1:
                logger.error(f"Hardware error in check_board (retry failed): controller={address}, function=check_board, error={type(e).__name__}: {e}")
            return False

def set_channel_duty_cycle(address: int, channel: int, duty_cycle: int):
    """
    Sets the duty cycle for a specific channel on a PCA9685 board.

    Args:
        address: The I2C address of the PCA9685 board.
        channel: The channel number to control (0-15).
        duty_cycle: The 16-bit duty cycle value (0-65535).

    Raises:
        ValueError: If the board is not found at the address.
        IOError: On other communication errors.
    """
    if not 0 <= channel <= 15:
        raise ValueError(f"Channel must be between 0 and 15 inclusive, got {channel}")
    if not 0 <= duty_cycle <= 65535:
        raise ValueError(f"Duty cycle must be between 0 and 65535 inclusive, got {duty_cycle}")
    
    # Check cache to see if value has changed
    manager = get_manager()
    if address in manager._channel_cache and channel in manager._channel_cache[address]:
        cached_value = manager._channel_cache[address][channel]
        if cached_value == duty_cycle:
            logger.info(f"HARDWARE_WRITE_SKIP: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle} (no change from cached value)")
            return  # Value hasn't changed, skip hardware write
    
    logger.info(f"HARDWARE_WRITE_START: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
    
    for attempt in range(2):  # Try once, retry once
        try:
            pca = manager.get_controller(address)
            logger.info(f"HARDWARE_WRITE_ATTEMPT: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, Attempt={attempt+1}")
            
            # INFO level logging for hardware write confirmation
            logger.info(f"Executing hardware write: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
            
            # The adafruit_pca9685 library expects a 16-bit value.
            pca.channels[channel].duty_cycle = duty_cycle
            
            logger.info(f"HARDWARE_WRITE_SUCCESS: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, Adafruit library call completed successfully")
            
            # Update cache after successful write
            if address not in manager._channel_cache:
                manager._channel_cache[address] = {}
            manager._channel_cache[address][channel] = duty_cycle
            return  # Success, exit the retry loop
        except (ValueError, IOError) as e:
            logger.error(f"HARDWARE_WRITE_ERROR: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, Attempt={attempt+1}, Error={type(e).__name__}: {e}")
            if attempt == 0:
                logger.error(f"Hardware error in set_channel_duty_cycle: controller={address}, channel={channel}, function=set_channel_duty_cycle, error={type(e).__name__}: {e}")
            elif attempt == 1:
                logger.error(f"Hardware error in set_channel_duty_cycle (retry failed): controller={address}, channel={channel}, function=set_channel_duty_cycle, error={type(e).__name__}: {e}")
                # Re-raise to be handled by the API layer.
                raise e

def set_frequency(address: int, frequency: int):
    """
    Sets the PWM frequency for a PCA9685 board.

    Args:
        address: The I2C address of the PCA9685 board.
        frequency: The PWM frequency in Hz (24-1526 Hz).

    Raises:
        ValueError: If the board is not found at the address or frequency is invalid.
        IOError: On other communication errors.
    """
    if not 24 <= frequency <= 1526:
        raise ValueError(f"Frequency must be between 24 and 1526 inclusive, got {frequency}")
    
    logger.info(f"HARDWARE_FREQ_START: I2C=0x{address:02X}, Frequency={frequency}Hz")
    
    for attempt in range(2):  # Try once, retry once
        try:
            manager = get_manager()
            pca = manager.get_controller(address)
            logger.info(f"HARDWARE_FREQ_ATTEMPT: I2C=0x{address:02X}, Frequency={frequency}Hz, Attempt={attempt+1}")
            
            # INFO level logging for hardware write confirmation
            logger.info(f"Executing hardware write: I2C=0x{address:02X}, Frequency={frequency}Hz")
            
            pca.frequency = frequency
            
            logger.info(f"HARDWARE_FREQ_SUCCESS: I2C=0x{address:02X}, Frequency={frequency}Hz, Adafruit library call completed successfully")
            return  # Success, exit the retry loop
        except (ValueError, IOError) as e:
            logger.error(f"HARDWARE_FREQ_ERROR: I2C=0x{address:02X}, Frequency={frequency}Hz, Attempt={attempt+1}, Error={type(e).__name__}: {e}")
            if attempt == 0:
                logger.error(f"Hardware error in set_frequency: controller={address}, function=set_frequency, error={type(e).__name__}: {e}")
            elif attempt == 1:
                logger.error(f"Hardware error in set_frequency (retry failed): controller={address}, function=set_frequency, error={type(e).__name__}: {e}")
                # Re-raise to be handled by the API layer.
                raise e

def get_current_duty_cycle(address: int, channel: int) -> int:
    """
    Reads the current duty cycle for a specific channel on a PCA9685 board.

    Args:
        address: The I2C address of the PCA9685 board.
        channel: The channel number to read (0-15).

    Returns:
        The current 16-bit duty cycle value (0-65535).

    Raises:
        ValueError: If the board is not found at the address.
        IOError: On other communication errors.
    """
    if not 0 <= channel <= 15:
        raise ValueError(f"Channel must be between 0 and 15 inclusive, got {channel}")
    
    for attempt in range(2):  # Try once, retry once
        try:
            manager = get_manager()
            pca = manager.get_controller(address)
            return pca.channels[channel].duty_cycle
        except (ValueError, IOError) as e:
            if attempt == 0:
                logger.error(f"Hardware error in get_current_duty_cycle: controller={address}, channel={channel}, function=get_current_duty_cycle, error={type(e).__name__}: {e}")
            elif attempt == 1:
                logger.error(f"Hardware error in get_current_duty_cycle (retry failed): controller={address}, channel={channel}, function=get_current_duty_cycle, error={type(e).__name__}: {e}")
                # Re-raise to be handled by the API layer.
                raise e 

def set_multiple_channels_duty_cycle(address: int, channel_duty_cycles: dict):
    """
    Sets the duty cycle for multiple channels on a PCA9685 board in a single operation.

    Args:
        address: The I2C address of the PCA9685 board.
        channel_duty_cycles: Dictionary mapping channel numbers (0-15) to duty cycle values (0-65535).

    Raises:
        ValueError: If the board is not found at the address or any channel/duty cycle values are invalid.
        IOError: On other communication errors.
    """
    if not channel_duty_cycles:
        return  # No channels to set
    
    # Validate all channel and duty cycle values
    for channel, duty_cycle in channel_duty_cycles.items():
        if not 0 <= channel <= 15:
            raise ValueError(f"Channel must be between 0 and 15 inclusive, got {channel}")
        if not 0 <= duty_cycle <= 65535:
            raise ValueError(f"Duty cycle must be between 0 and 65535 inclusive, got {duty_cycle}")
    
    logger.info(f"HARDWARE_BULK_START: I2C=0x{address:02X}, Channels={channel_duty_cycles}")
    
    # Filter channels that have actually changed
    manager = get_manager()
    changed_channels = {}
    
    for channel, duty_cycle in channel_duty_cycles.items():
        if address in manager._channel_cache and channel in manager._channel_cache[address]:
            cached_value = manager._channel_cache[address][channel]
            if cached_value == duty_cycle:
                logger.info(f"HARDWARE_BULK_SKIP: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle} (no change from cached value)")
                continue  # Skip this channel, value hasn't changed
        changed_channels[channel] = duty_cycle
    
    if not changed_channels:
        logger.info(f"HARDWARE_BULK_SKIP_ALL: I2C=0x{address:02X}, No duty cycle changes needed")
        return  # No changes needed
    
    logger.info(f"HARDWARE_BULK_WRITE: I2C=0x{address:02X}, ChangedChannels={changed_channels}")
    
    for attempt in range(2):  # Try once, retry once
        try:
            pca = manager.get_controller(address)
            logger.info(f"HARDWARE_BULK_ATTEMPT: I2C=0x{address:02X}, ChangedChannels={changed_channels}, Attempt={attempt+1}")
            
            # Set all changed channels in a loop using minimum hardware accesses
            for channel, duty_cycle in changed_channels.items():
                logger.info(f"HARDWARE_BULK_CHANNEL: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
                
                # INFO level logging for hardware write confirmation
                logger.info(f"Executing hardware write: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
                
                pca.channels[channel].duty_cycle = duty_cycle
                logger.info(f"HARDWARE_BULK_CHANNEL_SUCCESS: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, Adafruit library call completed")
                # Update cache after successful write
                if address not in manager._channel_cache:
                    manager._channel_cache[address] = {}
                manager._channel_cache[address][channel] = duty_cycle
            
            logger.info(f"HARDWARE_BULK_SUCCESS: I2C=0x{address:02X}, All {len(changed_channels)} channels written successfully")
            return  # Success, exit the retry loop
        except (ValueError, IOError) as e:
            logger.error(f"HARDWARE_BULK_ERROR: I2C=0x{address:02X}, ChangedChannels={changed_channels}, Attempt={attempt+1}, Error={type(e).__name__}: {e}")
            if attempt == 0:
                logger.error(f"Hardware error in set_multiple_channels_duty_cycle: controller={address}, function=set_multiple_channels_duty_cycle, error={type(e).__name__}: {e}")
            elif attempt == 1:
                logger.error(f"Hardware error in set_multiple_channels_duty_cycle (retry failed): controller={address}, function=set_multiple_channels_duty_cycle, error={type(e).__name__}: {e}")
                # Re-raise to be handled by the API layer.
                raise e

def reconnect_controller(address: int) -> bool:
    """
    Attempt to reconnect to a previously failed controller.
    
    Args:
        address: The I2C address of the controller to reconnect.
        
    Returns:
        True if reconnection was successful, False otherwise.
    """
    try:
        manager = get_manager()
        manager.remove_controller(address)  # Remove from cache to force recreation
        manager.get_controller(address)  # Attempt to recreate
        logger.info(f"Successfully reconnected to controller at 0x{address:02X}")
        return True
    except Exception as e:
        logger.error(f"Failed to reconnect to controller at 0x{address:02X}: {e}")
        return False

def get_manager_status() -> Dict[str, Any]:
    """Get the current status of the hardware manager."""
    try:
        manager = get_manager()
        return manager.get_status()
    except Exception as e:
        return {
            "error": f"Failed to get manager status: {str(e)}",
            "manager_available": False
        }

def perform_synchronous_hardware_write(address: int, channel: int, duty_cycle: int) -> bool:
    """
    Perform a synchronous hardware write from the main thread.
    This function ensures all hardware access happens in the main thread context.
    
    Args:
        address: The I2C address of the PCA9685 board.
        channel: The channel number to control (0-15).
        duty_cycle: The 16-bit duty cycle value (0-65535).
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Validate inputs
        if not 0 <= channel <= 15:
            logger.error(f"Invalid channel {channel} for address {hex(address)}")
            return False
        if not 0 <= duty_cycle <= 65535:
            logger.error(f"Invalid duty cycle {duty_cycle} for address {hex(address)}, channel {channel}")
            return False
        
        # Get the manager and perform the write
        manager = get_manager()
        
        # Check cache to see if value has changed
        if address in manager._channel_cache and channel in manager._channel_cache[address]:
            cached_value = manager._channel_cache[address][channel]
            if cached_value == duty_cycle:
                logger.debug(f"SYNC_HARDWARE_SKIP: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle} (no change)")
                return True  # Value hasn't changed, consider it successful
        
        logger.info(f"SYNC_HARDWARE_WRITE: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
        
        # Perform the hardware write
        pca = manager.get_controller(address)
        
        # INFO level logging for hardware write confirmation
        logger.info(f"Executing hardware write: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
        
        # The actual hardware write
        pca.channels[channel].duty_cycle = duty_cycle
        
        # Update cache after successful write
        if address not in manager._channel_cache:
            manager._channel_cache[address] = {}
        manager._channel_cache[address][channel] = duty_cycle
        
        logger.info(f"SYNC_HARDWARE_SUCCESS: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
        return True
        
    except Exception as e:
        logger.error(f"SYNC_HARDWARE_ERROR: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, Error={type(e).__name__}: {e}")
        return False 