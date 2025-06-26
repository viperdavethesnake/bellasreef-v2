import board
import busio
from adafruit_pca9685 import PCA9685
from contextlib import contextmanager

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
    try:
        with get_i2c_bus() as i2c:
            # The constructor for PCA9685 will raise a ValueError if the device
            # is not found at the specified address.
            PCA9685(i2c, address=address)
            return True
    except ValueError:
        # This typically means the device was not found.
        return False
    except Exception:
        # Catch any other unexpected errors during I2C communication.
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
    try:
        with get_i2c_bus() as i2c:
            pca = PCA9685(i2c, address=address)
            # The adafruit_pca9685 library expects a 16-bit value.
            pca.channels[channel].duty_cycle = duty_cycle
    except (ValueError, IOError) as e:
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
    try:
        with get_i2c_bus() as i2c:
            pca = PCA9685(i2c, address=address)
            pca.frequency = frequency
    except (ValueError, IOError) as e:
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
    try:
        with get_i2c_bus() as i2c:
            pca = PCA9685(i2c, address=address)
            return pca.channels[channel].duty_cycle
    except (ValueError, IOError) as e:
        # Re-raise to be handled by the API layer.
        raise e 