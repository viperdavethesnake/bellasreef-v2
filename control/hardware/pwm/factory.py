import os
import re
from typing import Optional, Dict, Any
from control.hardware.pwm.base import PWMController, PWMControllerType
from control.hardware.pwm.pi_legacy import RPiLegacyPWMController
from control.hardware.pwm.pi_rp1 import RP1PWMController
from control.hardware.pwm.pca9685 import PCA9685Controller
from control.hardware.pwm.noop import NoopPWMController
from shared.core.config import settings

class PWMControllerFactory:
    """Factory for creating PWM controllers based on explicit configuration."""
    
    _instance: Optional[PWMController] = None
    
    @classmethod
    def _validate_configuration(cls) -> None:
        """
        Validate PWM configuration and raise clear error messages.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Check platform configuration
        if settings.RPI_PLATFORM not in ["legacy", "rpi5", "none"]:
            raise ValueError(
                f"Invalid RPI_PLATFORM: {settings.RPI_PLATFORM}. "
                f"Must be one of: legacy, rpi5, none"
            )
        
        # Check GPIO pin configuration for Pi platforms
        if settings.RPI_PLATFORM in ["legacy", "rpi5"]:
            if not settings.PWM_GPIO_PIN_LIST:
                raise ValueError(
                    f"RPI_PLATFORM={settings.RPI_PLATFORM} requires PWM_GPIO_PINS to be configured. "
                    f"Set PWM_GPIO_PINS to comma-separated BCM GPIO numbers (e.g., '18,19')"
                )
            
            # Validate GPIO pins for the specific platform
            if settings.RPI_PLATFORM == "legacy":
                # Legacy Pi: Only hardware PWM pins (12, 13, 18, 19)
                valid_pins = [12, 13, 18, 19]
                invalid_pins = [pin for pin in settings.PWM_GPIO_PIN_LIST if pin not in valid_pins]
                if invalid_pins:
                    raise ValueError(
                        f"Invalid GPIO pins for legacy Pi: {invalid_pins}. "
                        f"Legacy Pi only supports hardware PWM on pins: {valid_pins}"
                    )
            
            elif settings.RPI_PLATFORM == "rpi5":
                # Pi 5: All GPIO pins support PWM via RP1
                # No specific validation needed beyond BCM range (already done in config)
                pass
        
        # Check PCA9685 configuration
        if settings.PCA9685_ENABLED:
            if not settings.PCA9685_ADDRESS:
                raise ValueError(
                    "PCA9685_ENABLED=true requires PCA9685_ADDRESS to be configured"
                )
    
    @classmethod
    def _get_controller_class(cls) -> type[PWMController]:
        """
        Determine which PWM controller class to use based on explicit configuration.
        
        Returns:
            PWMController class to instantiate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration first
        cls._validate_configuration()
        
        # Get platform from settings (no auto-detection)
        platform = settings.RPI_PLATFORM.lower()
        
        if platform == 'none':
            return NoopPWMController
        elif platform == 'legacy':
            return RPiLegacyPWMController
        elif platform == 'rpi5':
            return RP1PWMController
        else:
            # This should never happen due to validation above
            raise ValueError(f"Unsupported platform: {platform}")
    
    @classmethod
    def get_pwm_controller(cls) -> PWMController:
        """
        Get or create a singleton instance of the appropriate PWM controller.
        
        Returns:
            PWMController instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        if cls._instance is None:
            controller_class = cls._get_controller_class()
            
            # Create controller with appropriate parameters
            if controller_class == PCA9685Controller and settings.PCA9685_ENABLED:
                cls._instance = controller_class(
                    frequency=settings.PCA9685_FREQUENCY,
                    channels=settings.PWM_CHANNELS
                )
            else:
                cls._instance = controller_class(
                    frequency=settings.PWM_FREQUENCY,
                    channels=settings.PWM_CHANNELS
                )
        
        return cls._instance
    
    @classmethod
    def reset_pwm_controller(cls) -> None:
        """Reset the PWM controller singleton instance."""
        if cls._instance is not None:
            cls._instance = None
    
    @classmethod
    def get_configuration_summary(cls) -> Dict[str, str]:
        """
        Get a summary of the current PWM configuration.
        
        Returns:
            Dictionary with configuration details
        """
        try:
            cls._validate_configuration()
            controller_class = cls._get_controller_class()
            
            summary = {
                "platform": settings.RPI_PLATFORM,
                "controller": controller_class.__name__,
                "frequency": f"{settings.PWM_FREQUENCY}Hz",
                "channels": str(settings.PWM_CHANNELS),
                "status": "valid"
            }
            
            if settings.RPI_PLATFORM in ["legacy", "rpi5"]:
                summary["gpio_pins"] = settings.PWM_GPIO_PINS or "none"
            
            if settings.PCA9685_ENABLED:
                summary["pca9685"] = f"enabled (addr: {settings.PCA9685_ADDRESS})"
            else:
                summary["pca9685"] = "disabled"
            
            return summary
            
        except ValueError as e:
            return {
                "platform": settings.RPI_PLATFORM,
                "status": "invalid",
                "error": str(e)
            } 