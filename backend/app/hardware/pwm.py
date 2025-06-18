import board
import busio
from adafruit_pca9685 import PCA9685
from app.core.config import settings

class PWMController:
    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(self.i2c, address=0x40)
        self.pca.frequency = settings.PWM_FREQUENCY
        self.channels = {}

    async def set_channel(self, channel: int, value: float):
        """
        Set PWM channel value (0-1)
        """
        if not 0 <= channel < settings.PWM_CHANNELS:
            raise ValueError(f"Channel must be between 0 and {settings.PWM_CHANNELS-1}")
        if not 0 <= value <= 1:
            raise ValueError("Value must be between 0 and 1")
        
        # Convert 0-1 to 0-65535
        pwm_value = int(value * 65535)
        self.pca.channels[channel].duty_cycle = pwm_value
        self.channels[channel] = value

    async def get_channel(self, channel: int) -> float:
        """
        Get current PWM channel value
        """
        if not 0 <= channel < settings.PWM_CHANNELS:
            raise ValueError(f"Channel must be between 0 and {settings.PWM_CHANNELS-1}")
        return self.channels.get(channel, 0.0)

    async def all_off(self):
        """
        Turn off all channels
        """
        for channel in range(settings.PWM_CHANNELS):
            await self.set_channel(channel, 0.0) 