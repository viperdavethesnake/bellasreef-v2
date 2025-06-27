import board
import busio
from adafruit_pca9685 import PCA9685
from contextlib import contextmanager
from shared.utils.logger import get_logger

logger = get_logger(__name__)

class PCA9685ControllerManager:
    """
    Singleton manager for PCA9685 controllers.
    Manages a single shared I2C bus instance and maintains PCA9685 objects indexed by address.
    """
    _instance = None
    _i2c_bus = None
    _controllers = {}

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
            cls._i2c_bus = busio.I2C(board.SCL, board.SDA)
        
        if address not in cls._controllers:
            cls._controllers[address] = PCA9685(cls._i2c_bus, address=address)
        
        return cls._controllers[address]

    @classmethod
    def cleanup(cls):
        """Clean up I2C bus and controllers."""
        if cls._i2c_bus:
            cls._i2c_bus.deinit()
            cls._i2c_bus = None
            cls._controllers.clear()

@contextmanager
def get_i2c_bus():
    """Provides a context-managed I2C bus."""
    i2c = busio.I2C(board.SCL, board.SDA)
    try:
        yield i2c
    finally:
        i2c.deinit()

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
    
    logger.debug(f"Setting duty cycle: controller={address}, channel={channel}, duty_cycle={duty_cycle}")
    
    for attempt in range(2):  # Try once, retry once
        try:
            manager = PCA9685ControllerManager()
            pca = manager.get_controller(address)
            # The adafruit_pca9685 library expects a 16-bit value.
            pca.channels[channel].duty_cycle = duty_cycle
            return  # Success, exit the retry loop
        except (ValueError, IOError) as e:
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
    
    logger.debug(f"Setting frequency: controller={address}, frequency={frequency}Hz")
    
    for attempt in range(2):  # Try once, retry once
        try:
            manager = PCA9685ControllerManager()
            pca = manager.get_controller(address)
            pca.frequency = frequency
            return  # Success, exit the retry loop
        except (ValueError, IOError) as e:
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
    
    logger.debug(f"Setting multiple channels duty cycle: controller={address}, channels={channel_duty_cycles}")
    
    for attempt in range(2):  # Try once, retry once
        try:
            manager = PCA9685ControllerManager()
            pca = manager.get_controller(address)
            
            # Set all channels in a loop using minimum hardware accesses
            for channel, duty_cycle in channel_duty_cycles.items():
                pca.channels[channel].duty_cycle = duty_cycle
            
            return  # Success, exit the retry loop
        except (ValueError, IOError) as e:
            if attempt == 0:
                logger.error(f"Hardware error in set_multiple_channels_duty_cycle: controller={address}, function=set_multiple_channels_duty_cycle, error={type(e).__name__}: {e}")
            elif attempt == 1:
                logger.error(f"Hardware error in set_multiple_channels_duty_cycle (retry failed): controller={address}, function=set_multiple_channels_duty_cycle, error={type(e).__name__}: {e}")
                # Re-raise to be handled by the API layer.
                raise e 