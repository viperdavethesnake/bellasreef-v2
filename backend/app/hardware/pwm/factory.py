import os
import re
from typing import Optional, Dict, Any
from app.hardware.pwm.base import PWMController, PWMControllerType
from app.hardware.pwm.gpio import RPiLegacyPWMController
from app.hardware.pwm.rpi5 import Rpi5PWMController
from app.hardware.pwm.noop import NoopPWMController
from app.core.config import settings

class PWMControllerFactory:
    """Factory for creating PWM controllers based on configuration and hardware detection."""
    
    _instance: Optional[PWMController] = None
    
    @classmethod
    def _detect_raspberry_pi_model(cls) -> Optional[str]:
        """
        Detect Raspberry Pi model using hardware inspection.
        
        Returns:
            Model identifier ('legacy', 'rpi5', or None if not a Pi)
        """
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().lower()
            
            # Check for Pi 5 (uses RP1)
            if 'raspberry pi 5' in model:
                return 'rpi5'
            
            # Check for Pi 4 or earlier (uses legacy GPIO)
            if 'raspberry pi' in model:
                return 'legacy'
            
            return None
        except Exception:
            return None
    
    @classmethod
    def _get_controller_class(cls) -> type[PWMController]:
        """
        Determine which PWM controller class to use based on configuration.
        
        Returns:
            PWMController class to instantiate
        """
        # Get platform from settings
        platform = settings.RPI_PLATFORM.lower()
        
        if platform == 'none':
            return NoopPWMController
        elif platform == 'legacy':
            return RPiLegacyPWMController
        elif platform == 'rpi5':
            return Rpi5PWMController
        elif platform == 'auto':
            # Auto-detect platform
            pi_model = cls._detect_raspberry_pi_model()
            if pi_model == 'rpi5':
                return Rpi5PWMController
            elif pi_model == 'legacy':
                return RPiLegacyPWMController
            else:
                # If detection fails, fall back to no-op
                return NoopPWMController
        else:
            # Invalid platform setting, fall back to no-op
            return NoopPWMController
    
    @classmethod
    def get_pwm_controller(cls) -> PWMController:
        """
        Get or create a singleton instance of the appropriate PWM controller.
        
        Returns:
            PWMController instance
        """
        if cls._instance is None:
            controller_class = cls._get_controller_class()
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