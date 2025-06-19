import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import RPi.GPIO as GPIO
from app.hardware.device_base import BaseDevice, PollResult

class Outlet(BaseDevice):
    """
    Power outlet device supporting GPIO-controlled relays.
    Can be used for lights, pumps, heaters, etc.
    """
    
    def __init__(self, device_id: int, name: str, address: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(device_id, name, address, config)
        self.pin = int(self.address)
        self.active_high = self.config.get("active_high", True)
        self.current_state = False
        self._initialize_gpio()
    
    def _initialize_gpio(self):
        """Initialize GPIO pin for the outlet"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            
            # Set initial state to off
            initial_state = GPIO.HIGH if not self.active_high else GPIO.LOW
            GPIO.output(self.pin, initial_state)
            self.current_state = False
            
            self.logger.info(f"Initialized outlet on GPIO {self.pin} (active_high={self.active_high})")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO pin {self.pin}: {e}")
    
    async def poll(self) -> PollResult:
        """Get current outlet state"""
        try:
            # Read current GPIO state
            gpio_state = GPIO.input(self.pin)
            
            # Convert to logical state based on active_high setting
            if self.active_high:
                self.current_state = bool(gpio_state)
            else:
                self.current_state = not bool(gpio_state)
            
            metadata = {
                "pin": self.pin,
                "active_high": self.active_high,
                "gpio_state": gpio_state,
                "unit": "boolean"
            }
            
            return PollResult(
                success=True,
                value=1.0 if self.current_state else 0.0,
                metadata=metadata,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return PollResult(
                success=False,
                error=f"Failed to read outlet state: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    async def set_state(self, state: bool) -> bool:
        """Set outlet state (True = on, False = off)"""
        try:
            # Convert logical state to GPIO state
            if self.active_high:
                gpio_state = GPIO.HIGH if state else GPIO.LOW
            else:
                gpio_state = GPIO.LOW if state else GPIO.HIGH
            
            GPIO.output(self.pin, gpio_state)
            self.current_state = state
            
            self.logger.info(f"Set outlet {self.name} to {'ON' if state else 'OFF'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set outlet state: {e}")
            return False
    
    async def toggle(self) -> bool:
        """Toggle outlet state"""
        return await self.set_state(not self.current_state)
    
    async def test_connection(self) -> bool:
        """Test if the GPIO pin is accessible"""
        try:
            # Try to read the current state
            GPIO.input(self.pin)
            return True
            
        except Exception as e:
            self.logger.debug(f"Connection test failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            GPIO.cleanup(self.pin)
            self.logger.info(f"Cleaned up GPIO pin {self.pin}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup GPIO pin {self.pin}: {e}") 