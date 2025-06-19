from typing import Dict, List
import board
import busio
from adafruit_pca9685 import PCA9685
from app.hardware.pwm.base import PWMController, PWMControllerType
from app.core.config import settings

class RP1PWMController(PWMController):
    """PWM controller implementation for Raspberry Pi 5 with RP1 chip."""
    
    def __init__(self, frequency: int, channels: int):
        super().__init__(frequency, channels)
        self._i2c = None
        self._pca = None
        self._gpio_pins: List[int] = settings.PWM_GPIO_PIN_LIST
        self._initialized = False
        
        # Validate GPIO pins for Pi 5
        self._validate_gpio_pins()
    
    def _validate_gpio_pins(self) -> None:
        """Validate that configured GPIO pins are within BCM range for Pi 5."""
        # Pi 5 supports PWM on all GPIO pins via RP1
        # Just validate BCM range (1-40)
        invalid_pins = [pin for pin in self._gpio_pins if not (1 <= pin <= 40)]
        
        if invalid_pins:
            raise ValueError(
                f"Invalid GPIO pins for Pi 5: {invalid_pins}. "
                f"BCM GPIO pins must be between 1 and 40"
            )
    
    async def initialize(self) -> None:
        """Initialize I2C and PCA9685 hardware for Pi 5 RP1 PWM."""
        if self._initialized:
            return
        
        try:
            # Initialize I2C for RP1 PWM
            self._i2c = busio.I2C(board.SCL, board.SDA)
            self._pca = PCA9685(self._i2c, address=0x40)
            self._pca.frequency = self.frequency
            
            # Initialize all configured channels to 0
            for channel in range(len(self._gpio_pins)):
                self._pca.channels[channel].duty_cycle = 0
            
            self._initialized = True
            
        except Exception as e:
            # Clean up on failure
            await self.cleanup()
            raise RuntimeError(f"Failed to initialize RP1 PWM controller: {e}")
    
    async def cleanup(self) -> None:
        """Clean up I2C resources."""
        if not self._initialized:
            return
        
        try:
            if self._pca:
                await self.all_off()
            
            # Clean up I2C
            if self._i2c:
                self._i2c.deinit()
            
            # Clear state
            self._pca = None
            self._i2c = None
            self._channel_values.clear()
            self._initialized = False
            
        except Exception as e:
            raise RuntimeError(f"Failed to cleanup RP1 PWM controller: {e}")
    
    async def set_channel(self, channel: int, value: float) -> None:
        """Set PWM channel value using RP1 hardware PWM."""
        await super().set_channel(channel, value)
        
        if not self._initialized:
            raise RuntimeError("PWM controller not initialized")
        
        if channel >= len(self._gpio_pins):
            raise ValueError(f"Channel {channel} exceeds configured GPIO pins ({len(self._gpio_pins)})")
        
        try:
            # Convert 0-1 to 0-65535 for PCA9685
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
        await super().all_off()
        
        if not self._initialized:
            return
        
        try:
            for channel in range(len(self._gpio_pins)):
                await self.set_channel(channel, 0.0)
        except Exception as e:
            raise RuntimeError(f"Failed to turn off all channels: {e}")
    
    @property
    def controller_type(self) -> PWMControllerType:
        return PWMControllerType.RP1
    
    @property
    def hardware_info(self) -> Dict[str, str]:
        """Get detailed hardware information."""
        return {
            "type": "rp1",
            "driver": "RP1 Hardware PWM",
            "platform": "Raspberry Pi 5",
            "gpio_pins": ", ".join(str(pin) for pin in self._gpio_pins),
            "channels": str(len(self._gpio_pins)),
            "frequency": f"{self.frequency}Hz",
            "additional": f"RP1 PWM on BCM pins: {', '.join(str(pin) for pin in self._gpio_pins)}"
        } 