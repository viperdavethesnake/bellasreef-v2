from typing import Dict
from control.hardware.pwm.base import PWMController, PWMControllerType

class NoopPWMController(PWMController):
    """No-op PWM controller for testing and development."""
    
    def __init__(self, frequency: int, channels: int):
        super().__init__(frequency, channels)
    
    async def initialize(self) -> None:
        """Initialize the no-op controller."""
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up the no-op controller."""
        self._initialized = False
        self._channel_values.clear()
    
    async def set_channel(self, channel: int, value: float) -> None:
        """Set channel value (no-op)."""
        await super().set_channel(channel, value)
        self._channel_values[channel] = value
    
    async def get_channel(self, channel: int) -> float:
        """Get channel value."""
        await super().get_channel(channel)
        return self._channel_values.get(channel, 0.0)
    
    async def all_off(self) -> None:
        """Turn off all channels."""
        await super().all_off()
        self._channel_values.clear()
    
    @property
    def controller_type(self) -> PWMControllerType:
        return PWMControllerType.NONE
    
    @property
    def hardware_info(self) -> Dict[str, str]:
        return {
            "type": "none",
            "driver": "noop",
            "channels": str(self.channels),
            "frequency": f"{self.frequency}Hz",
            "additional": "Development/Testing mode"
        } 