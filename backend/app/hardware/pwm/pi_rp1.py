from typing import Dict
import board
import busio
from adafruit_pca9685 import PCA9685
from app.hardware.pwm.base import PWMController

class RP1PWMController(PWMController):
    """PWM controller implementation for Raspberry Pi 5 with RP1 chip."""
    
    def __init__(self, frequency: int, channels: int):
        super().__init__(frequency, channels)
        self._i2c = None
        self._pca = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize I2C and PCA9685 hardware."""
        if self._initialized:
            return
        
        try:
            self._i2c = busio.I2C(board.SCL, board.SDA)
            self._pca = PCA9685(self._i2c, address=0x40)
            self._pca.frequency = self.frequency
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize RP1 PWM controller: {e}")
    
    async def cleanup(self) -> None:
        """Clean up I2C resources."""
        if not self._initialized:
            return
        
        try:
            if self._pca:
                await self.all_off()
            self._pca = None
            self._i2c = None
            self._channel_values.clear()
            self._initialized = False
        except Exception as e:
            raise RuntimeError(f"Failed to cleanup RP1 PWM controller: {e}")
    
    async def set_channel(self, channel: int, value: float) -> None:
        """Set PWM channel value using PCA9685."""
        await super().set_channel(channel, value)
        
        if not self._initialized:
            raise RuntimeError("PWM controller not initialized")
        
        try:
            # Convert 0-1 to 0-65535
            pwm_value = int(value * 65535)
            self._pca.channels[channel].duty_cycle = pwm_value
            self._channel_values[channel] = value
        except Exception as e:
            raise RuntimeError(f"Failed to set channel {channel}: {e}")
    
    async def get_channel(self, channel: int) -> float:
        """Get current PWM channel value."""
        await super().get_channel(channel)
        return self._channel_values.get(channel, 0.0)
    
    async def all_off(self) -> None:
        """Turn off all channels."""
        if not self._initialized:
            return
        
        try:
            for channel in range(self.channels):
                await self.set_channel(channel, 0.0)
        except Exception as e:
            raise RuntimeError(f"Failed to turn off all channels: {e}")
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def hardware_info(self) -> Dict[str, str]:
        return {
            "type": "rp1",
            "driver": "PCA9685",
            "channels": str(self.channels),
            "frequency": f"{self.frequency}Hz"
        } 