import board
import busio
from adafruit_pca9685 import PCA9685
from typing import Dict, Optional
from app.hardware.pwm.base import PWMController, PWMControllerType
from app.core.config import settings

class PCA9685Controller(PWMController):
    """PCA9685 I2C PWM controller implementation."""
    
    def __init__(self, frequency: Optional[int] = None, channels: int = 16):
        """
        Initialize PCA9685 controller.
        
        Args:
            frequency: PWM frequency in Hz (defaults to PCA9685_FREQUENCY from settings)
            channels: Number of channels (defaults to 16 for PCA9685)
        """
        # Validate that PCA9685 is explicitly enabled
        if not settings.PCA9685_ENABLED:
            raise ValueError(
                "PCA9685 controller requires PCA9685_ENABLED=true in configuration"
            )
        
        self._i2c: Optional[busio.I2C] = None
        self._pca: Optional[PCA9685] = None
        self._address = int(settings.PCA9685_ADDRESS, 16)
        
        super().__init__(
            frequency or settings.PCA9685_FREQUENCY,
            channels
        )
    
    async def initialize(self) -> None:
        """Initialize the PCA9685 controller."""
        if self._initialized:
            return
        
        try:
            self._i2c = busio.I2C(board.SCL, board.SDA)
            self._pca = PCA9685(self._i2c, address=self._address)
            self._pca.frequency = self.frequency
            
            # Initialize all channels to 0
            for channel in range(self.channels):
                self._pca.channels[channel].duty_cycle = 0
            
            self._initialized = True
            
        except Exception as e:
            # Clean up on failure
            await self.cleanup()
            raise RuntimeError(f"Failed to initialize PCA9685: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up PCA9685 resources."""
        if self._initialized:
            await self.all_off()
            
            # Clean up I2C
            if self._i2c:
                self._i2c.deinit()
            
            self._pca = None
            self._i2c = None
            self._initialized = False
    
    async def set_channel(self, channel: int, value: float) -> None:
        """Set PCA9685 channel value."""
        await super().set_channel(channel, value)
        if not self._pca:
            raise RuntimeError("PCA9685 not initialized")
        
        # Convert 0-1 value to 0-65535 for PCA9685
        pwm_value = int(value * 65535)
        self._pca.channels[channel].duty_cycle = pwm_value
        self._channel_values[channel] = value
    
    async def get_channel(self, channel: int) -> float:
        """Get PCA9685 channel value."""
        await super().get_channel(channel)
        if not self._pca:
            raise RuntimeError("PCA9685 not initialized")
        
        # Convert 0-65535 value to 0-1
        pwm_value = self._pca.channels[channel].duty_cycle
        return pwm_value / 65535.0
    
    async def all_off(self) -> None:
        """Turn off all PCA9685 channels."""
        await super().all_off()
        if not self._pca:
            raise RuntimeError("PCA9685 not initialized")
        
        for channel in range(self.channels):
            self._pca.channels[channel].duty_cycle = 0
        self._channel_values.clear()
    
    @property
    def controller_type(self) -> PWMControllerType:
        return PWMControllerType.PCA9685
    
    @property
    def hardware_info(self) -> Dict[str, str]:
        """Get detailed hardware information."""
        return {
            "type": "pca9685",
            "driver": "adafruit-circuitpython-pca9685",
            "platform": "External I2C Controller",
            "channels": str(self.channels),
            "frequency": f"{self.frequency}Hz",
            "address": f"0x{self._address:02x}",
            "additional": f"I2C-based PWM controller at address 0x{self._address:02x}"
        } 