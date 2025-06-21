"""
Abstract SmartOutlet Driver Base Class

This module defines the base class that all smart outlet drivers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..models import SmartOutletState


class AbstractSmartOutletDriver(ABC):
    """
    Abstract base class for smart outlet drivers.
    
    All driver implementations must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the driver.
        
        Args:
            device_id: Unique identifier for the device
            ip_address: IP address of the device
            auth_info: Optional authentication information
        """
        self.device_id = device_id
        self.ip_address = ip_address
        self.auth_info = auth_info or {}
    
    @abstractmethod
    async def turn_on(self) -> bool:
        """
        Turn on the outlet.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def turn_off(self) -> bool:
        """
        Turn off the outlet.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def toggle(self) -> bool:
        """
        Toggle the outlet state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_state(self) -> SmartOutletState:
        """
        Get the current state of the outlet.
        
        Returns:
            SmartOutletState: Current state information
        """
        pass
    
    @abstractmethod
    async def discover_device(self) -> Dict:
        """
        Discover and return device information.
        
        Returns:
            Dict: Device information including type, capabilities, etc.
        """
        pass 