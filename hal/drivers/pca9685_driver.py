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