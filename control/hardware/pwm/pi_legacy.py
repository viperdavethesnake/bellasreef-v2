from typing import Dict, List
import RPi.GPIO as GPIO
from control.hardware.pwm.base import PWMController, PWMControllerType
from shared.core.config import settings

class RPiLegacyPWMController(PWMController):
    """PWM controller implementation for Raspberry Pi 4 and earlier using hardware PWM."""
    
    def __init__(self, frequency: int, channels: int):
        super().__init__(frequency, channels)
        self._pwm_instances: Dict[int, GPIO.PWM] = {}
        self._gpio_pins: List[int] = settings.PWM_GPIO_PIN_LIST
        self._initialized = False
        
        # Validate GPIO pins for legacy Pi
        self._validate_gpio_pins()
    
    def _validate_gpio_pins(self) -> None:
        """Validate that configured GPIO pins support hardware PWM on legacy Pi."""
        # Legacy Pi hardware PWM pins: 12, 13, 18, 19
        valid_pins = [12, 13, 18, 19]
        invalid_pins = [pin for pin in self._gpio_pins if pin not in valid_pins]
        
        if invalid_pins:
            raise ValueError(
                f"Invalid GPIO pins for legacy Pi: {invalid_pins}. "
                f"Legacy Pi only supports hardware PWM on pins: {valid_pins}"
            )
        
        if len(self._gpio_pins) > len(valid_pins):
            raise ValueError(
                f"Too many GPIO pins configured: {len(self._gpio_pins)}. "
                f"Legacy Pi supports maximum {len(valid_pins)} hardware PWM pins"
            )
    
    async def initialize(self) -> None:
        """Initialize GPIO and PWM hardware."""
        if self._initialized:
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Initialize each GPIO pin for PWM
            for i, pin in enumerate(self._gpio_pins):
                GPIO.setup(pin, GPIO.OUT)
                pwm = GPIO.PWM(pin, self.frequency)
                pwm.start(0)  # Start with 0% duty cycle
                self._pwm_instances[i] = pwm
            
            self._initialized = True
            
        except Exception as e:
            # Clean up on failure
            await self.cleanup()
            raise RuntimeError(f"Failed to initialize legacy PWM controller: {e}")
    
    async def cleanup(self) -> None:
        """Clean up GPIO resources."""
        if not self._initialized:
            return
        
        try:
            # Stop all PWM instances
            for pwm in self._pwm_instances.values():
                pwm.stop()
            
            # Clean up GPIO
            GPIO.cleanup()
            
            # Clear state
            self._pwm_instances.clear()
            self._channel_values.clear()
            self._initialized = False
            
        except Exception as e:
            raise RuntimeError(f"Failed to cleanup legacy PWM controller: {e}")
    
    async def set_channel(self, channel: int, value: float) -> None:
        """Set PWM channel value using RPi.GPIO hardware PWM."""
        await super().set_channel(channel, value)
        
        if not self._initialized:
            raise RuntimeError("PWM controller not initialized")
        
        if channel >= len(self._gpio_pins):
            raise ValueError(f"Channel {channel} exceeds configured GPIO pins ({len(self._gpio_pins)})")
        
        try:
            # Convert 0-1 value to 0-100 for RPi.GPIO
            duty_cycle = value * 100
            self._pwm_instances[channel].ChangeDutyCycle(duty_cycle)
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
        return PWMControllerType.LEGACY
    
    @property
    def hardware_info(self) -> Dict[str, str]:
        """Get detailed hardware information."""
        return {
            "type": "legacy",
            "driver": "RPi.GPIO Hardware PWM",
            "platform": "Raspberry Pi 4 and earlier",
            "gpio_pins": ", ".join(str(pin) for pin in self._gpio_pins),
            "channels": str(len(self._gpio_pins)),
            "frequency": f"{self.frequency}Hz",
            "additional": f"Hardware PWM on BCM pins: {', '.join(str(pin) for pin in self._gpio_pins)}"
        } 