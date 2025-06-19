from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PollResult(BaseModel):
    """Result of a device polling operation"""
    success: bool
    value: Optional[float] = None
    json_value: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime

class BaseDevice(ABC):
    """
    Base class for all device plugins.
    Each device type should inherit from this and implement the required methods.
    """
    
    def __init__(self, device_id: int, name: str, address: str, config: Optional[Dict[str, Any]] = None):
        self.device_id = device_id
        self.name = name
        self.address = address
        self.config = config or {}
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")
    
    @abstractmethod
    async def poll(self) -> PollResult:
        """
        Poll the device and return the result.
        This method must be implemented by each device type.
        
        Returns:
            PollResult: The result of the polling operation
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if the device is reachable and responding.
        This method must be implemented by each device type.
        
        Returns:
            bool: True if device is reachable, False otherwise
        """
        pass
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Get basic information about the device.
        Can be overridden by subclasses to provide device-specific info.
        
        Returns:
            Dict[str, Any]: Device information
        """
        return {
            "device_id": self.device_id,
            "name": self.name,
            "address": self.address,
            "device_type": self.__class__.__name__,
            "config": self.config
        }
    
    async def safe_poll(self) -> PollResult:
        """
        Safely poll the device with error handling.
        This is the main method that should be called by the poller.
        
        Returns:
            PollResult: The result of the polling operation
        """
        timestamp = datetime.utcnow()
        
        try:
            self.logger.debug(f"Polling device {self.name} ({self.address})")
            result = await self.poll()
            result.timestamp = timestamp
            
            if result.success:
                self.logger.debug(f"Successfully polled {self.name}: {result.value or result.json_value}")
            else:
                self.logger.warning(f"Failed to poll {self.name}: {result.error}")
            
            return result
            
        except Exception as e:
            error_msg = f"Exception while polling {self.name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return PollResult(
                success=False,
                error=error_msg,
                timestamp=timestamp
            )
    
    async def safe_test_connection(self) -> bool:
        """
        Safely test device connection with error handling.
        
        Returns:
            bool: True if device is reachable, False otherwise
        """
        try:
            self.logger.debug(f"Testing connection to {self.name} ({self.address})")
            result = await self.test_connection()
            
            if result:
                self.logger.debug(f"Successfully connected to {self.name}")
            else:
                self.logger.warning(f"Failed to connect to {self.name}")
            
            return result
            
        except Exception as e:
            error_msg = f"Exception while testing connection to {self.name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False 