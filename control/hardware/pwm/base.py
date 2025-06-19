from abc import ABC, abstractmethod
from typing import Dict, Optional, Literal
from enum import Enum

class PWMControllerType(Enum):
    """Enum for different PWM controller types."""
    NONE = "none"
    LEGACY = "legacy"
    RP1 = "rp1"
    PCA9685 = "pca9685"

class PWMController(ABC):
    """Abstract base class for PWM controllers."""
    
    def __init__(self, frequency: int, channels: int):
        self.frequency = frequency
        self.channels = channels
        self._channel_values: Dict[int, float] = {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the PWM controller hardware.
        Must be called before using the controller.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up hardware resources.
        Should be called when the controller is no longer needed.
        """
        pass
    
    @abstractmethod
    async def set_channel(self, channel: int, value: float) -> None:
        """
        Set PWM channel value (0-1).
        
        Args:
            channel: Channel number (0 to channels-1)
            value: Duty cycle (0.0 to 1.0)
            
        Raises:
            ValueError: If channel or value is invalid
            RuntimeError: If controller is not initialized
        """
        if not 0 <= channel < self.channels:
            raise ValueError(f"Channel must be between 0 and {self.channels-1}")
        if not 0 <= value <= 1:
            raise ValueError("Value must be between 0 and 1")
        if not self._initialized:
            raise RuntimeError("PWM controller not initialized")
    
    @abstractmethod
    async def get_channel(self, channel: int) -> float:
        """
        Get current PWM channel value.
        
        Args:
            channel: Channel number (0 to channels-1)
            
        Returns:
            Current duty cycle (0.0 to 1.0)
            
        Raises:
            ValueError: If channel is invalid
            RuntimeError: If controller is not initialized
        """
        if not 0 <= channel < self.channels:
            raise ValueError(f"Channel must be between 0 and {self.channels-1}")
        if not self._initialized:
            raise RuntimeError("PWM controller not initialized")
        return self._channel_values.get(channel, 0.0)
    
    @abstractmethod
    async def all_off(self) -> None:
        """
        Turn off all channels.
        
        Raises:
            RuntimeError: If controller is not initialized
        """
        if not self._initialized:
            raise RuntimeError("PWM controller not initialized")
    
    @property
    def is_initialized(self) -> bool:
        """Check if the controller is initialized."""
        return self._initialized
    
    @property
    @abstractmethod
    def controller_type(self) -> PWMControllerType:
        """Get the type of this controller."""
        pass
    
    @property
    @abstractmethod
    def hardware_info(self) -> Dict[str, str]:
        """
        Get information about the hardware implementation.
        
        Returns:
            Dictionary containing hardware information:
            - type: Controller type
            - driver: Driver name
            - channels: Number of channels
            - frequency: PWM frequency
            - additional: Any additional hardware-specific info
        """
        pass 