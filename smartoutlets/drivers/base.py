"""
Abstract SmartOutlet Driver Base Class

This module defines the base class that all smart outlet drivers must implement.
It provides the interface and retry logic for all driver implementations.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Coroutine, Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared.core.config import settings
from ..exceptions import OutletConnectionError, OutletTimeoutError
from ..schemas import SmartOutletState


class AbstractSmartOutletDriver(ABC):
    """
    Abstract base class for smart outlet drivers.
    
    All driver implementations must inherit from this class and implement
    the required methods for device control and state retrieval.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the driver.
        
        Args:
            device_id (str): Unique identifier for the device
            ip_address (str): IP address of the device
            auth_info (Optional[Dict]): Optional authentication information
        """
        self.device_id = device_id
        self.ip_address = ip_address
        self.auth_info = auth_info or {}
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{device_id}")
    
    @retry(
        stop=stop_after_attempt(settings.OUTLET_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((OutletConnectionError, asyncio.TimeoutError)),
        before_sleep=lambda retry_state: retry_state.outcome.exception() and 
            logging.getLogger(f"AbstractSmartOutletDriver.{retry_state.args[0].device_id}").warning(
                f"Retry attempt {retry_state.attempt_number} for {retry_state.fn.__name__} "
                f"after {retry_state.outcome.exception()}"
            )
    )
    async def _perform_network_action(self, action_coro: Coroutine) -> Any:
        """
        Perform a network action with retry logic and timeout.
        
        Args:
            action_coro (Coroutine): The coroutine to execute
            
        Returns:
            Any: The result of the action
            
        Raises:
            OutletConnectionError: If the action fails after all retries
            OutletTimeoutError: If the action times out
        """
        try:
            return await asyncio.wait_for(action_coro, timeout=settings.OUTLET_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout after {settings.OUTLET_TIMEOUT_SECONDS}s for device {self.device_id}")
            raise OutletTimeoutError(f"Operation timed out after {settings.OUTLET_TIMEOUT_SECONDS} seconds")
        except Exception as e:
            self.logger.error(f"Network error for device {self.device_id}: {e}")
            raise OutletConnectionError(f"Network operation failed: {e}")
    
    async def turn_on(self) -> bool:
        """
        Turn on the outlet with retry logic.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return await self._perform_network_action(self._turn_on_implementation())
    
    async def turn_off(self) -> bool:
        """
        Turn off the outlet with retry logic.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return await self._perform_network_action(self._turn_off_implementation())
    
    async def toggle(self) -> bool:
        """
        Toggle the outlet state with retry logic.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return await self._perform_network_action(self._toggle_implementation())
    
    async def get_state(self) -> SmartOutletState:
        """
        Get the current state of the outlet with retry logic.
        
        Returns:
            SmartOutletState: Current state information
        """
        return await self._perform_network_action(self._get_state_implementation())
    
    @abstractmethod
    async def _turn_on_implementation(self) -> bool:
        """
        Implementation of turn on operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def _turn_off_implementation(self) -> bool:
        """
        Implementation of turn off operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def _toggle_implementation(self) -> bool:
        """
        Implementation of toggle operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def _get_state_implementation(self) -> SmartOutletState:
        """
        Implementation of get state operation.
        
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