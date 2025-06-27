import board
import busio
import os
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
    Singleton manager for PCA9685 controllers.
    Manages a single shared I2C bus instance and maintains PCA9685 objects indexed by address.
    """
    _instance = None
    _i2c_bus = None
    _controllers = {}
    _channel_cache = {}  # {address: {channel: last_duty_cycle}}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PCA9685ControllerManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True

    @classmethod
    def get_controller(cls, address: int) -> PCA9685:
        """
        Get or create a PCA9685 controller for the given address.
        
        Args:
            address: The I2C address of the PCA9685 board.
            
        Returns:
            PCA9685 object for the given address.
        """
        if cls._i2c_bus is None:
            logger.info(f"HARDWARE_INIT: Creating new I2C bus for PCA9685 controllers")
            cls._i2c_bus = busio.I2C(board.SCL, board.SDA)
        
        if address not in cls._controllers:
            logger.info(f"HARDWARE_INIT: Creating new PCA9685 controller at I2C address 0x{address:02X}")
            cls._controllers[address] = PCA9685(cls._i2c_bus, address=address)
            cls._channel_cache[address] = {}  # Initialize cache for this controller
            logger.info(f"HARDWARE_INIT: Successfully created PCA9685 controller at 0x{address:02X}")
        else:
            logger.debug(f"HARDWARE_INIT: Reusing existing PCA9685 controller at 0x{address:02X}")
        
        return cls._controllers[address]

    @classmethod
    def cleanup(cls):
        """Clean up I2C bus and controllers."""
        if cls._i2c_bus:
            cls._i2c_bus.deinit()
            cls._i2c_bus = None
            cls._controllers.clear()
            cls._channel_cache.clear()

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
            manager = PCA9685ControllerManager()
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
    manager = PCA9685ControllerManager()
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
            
            # WARNING level logging and side effect for hardware write confirmation
            logger.warning(f"HARDWARE_WRITE_EXECUTING: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, About to write to PCA9685 hardware")
            try:
                os.system("touch /tmp/hal-api-write")
                logger.warning(f"HARDWARE_WRITE_SIDE_EFFECT: Created /tmp/hal-api-write to confirm hardware write execution")
            except Exception as side_effect_error:
                logger.warning(f"HARDWARE_WRITE_SIDE_EFFECT_FAILED: Could not create side effect file: {side_effect_error}")
            
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
            manager = PCA9685ControllerManager()
            pca = manager.get_controller(address)
            logger.info(f"HARDWARE_FREQ_ATTEMPT: I2C=0x{address:02X}, Frequency={frequency}Hz, Attempt={attempt+1}")
            
            # WARNING level logging and side effect for hardware write confirmation
            logger.warning(f"HARDWARE_FREQ_EXECUTING: I2C=0x{address:02X}, Frequency={frequency}Hz, About to write to PCA9685 hardware")
            try:
                os.system("touch /tmp/hal-api-write")
                logger.warning(f"HARDWARE_FREQ_SIDE_EFFECT: Created /tmp/hal-api-write to confirm frequency write execution")
            except Exception as side_effect_error:
                logger.warning(f"HARDWARE_FREQ_SIDE_EFFECT_FAILED: Could not create side effect file: {side_effect_error}")
            
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
            manager = PCA9685ControllerManager()
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
    manager = PCA9685ControllerManager()
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
                
                # WARNING level logging and side effect for hardware write confirmation
                logger.warning(f"HARDWARE_BULK_EXECUTING: I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, About to write to PCA9685 hardware")
                try:
                    os.system("touch /tmp/hal-api-write")
                    logger.warning(f"HARDWARE_BULK_SIDE_EFFECT: Created /tmp/hal-api-write to confirm bulk hardware write execution")
                except Exception as side_effect_error:
                    logger.warning(f"HARDWARE_BULK_SIDE_EFFECT_FAILED: Could not create side effect file: {side_effect_error}")
                
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