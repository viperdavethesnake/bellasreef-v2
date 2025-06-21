"""
SmartOutlet Manager Module

This module provides the main SmartOutletManager class that handles outlet operations
with support for multiple driver types (Kasa, Shelly, VeSync).
"""

import logging
from typing import Callable, Dict, Type

from sqlalchemy.ext.asyncio import AsyncSession

from . import config
from .drivers import AbstractSmartOutletDriver, KasaDriver, ShellyDriver, VeSyncDriver
from .exceptions import DriverNotImplementedError, OutletNotFoundError
from .models import SmartOutlet, SmartOutletState


# Driver registry mapping driver types to their classes
DRIVER_REGISTRY: Dict[str, Type[AbstractSmartOutletDriver]] = {
    "kasa": KasaDriver,
    "shelly": ShellyDriver,
    "vesync": VeSyncDriver,
}


class SmartOutletManager:
    """
    Main manager class for smart outlet operations.
    
    Handles enable/disable checks, driver instantiation, and real-time outlet control.
    """
    
    def __init__(self, db_session_factory: Callable[[], AsyncSession], logger: logging.Logger):
        """
        Initialize the SmartOutletManager.
        
        Args:
            db_session_factory: Factory function to create async database sessions
            logger: Logger instance for the manager
        """
        self._db_session_factory = db_session_factory
        self._logger = logger
        self._active_drivers: Dict[str, AbstractSmartOutletDriver] = {}
        
        # Check if module is enabled
        if not config.SMART_OUTLETS_ENABLED:
            raise RuntimeError("SmartOutlets module is disabled via config.")
    
    async def _get_driver_instance(self, outlet_id: str) -> AbstractSmartOutletDriver:
        """
        Get or create a driver instance for the specified outlet.
        
        Args:
            outlet_id: The ID of the outlet to get the driver for
            
        Returns:
            AbstractSmartOutletDriver: The driver instance for the outlet
            
        Raises:
            OutletNotFoundError: If the outlet is not found in the database
            DriverNotImplementedError: If the driver type is disabled or not supported
        """
        # Return cached driver if already available
        if outlet_id in self._active_drivers:
            return self._active_drivers[outlet_id]
        
        # Open database session and load outlet
        async with self._db_session_factory() as session:
            outlet = await session.get(SmartOutlet, outlet_id)
            
            if not outlet:
                raise OutletNotFoundError(f"Outlet with ID {outlet_id} not found")
            
            # Check if driver type is enabled
            if not config.is_driver_enabled(outlet.driver_type):
                raise DriverNotImplementedError(
                    f"Driver type '{outlet.driver_type}' is disabled via config"
                )
            
            # Get driver class from registry
            driver_class = DRIVER_REGISTRY.get(outlet.driver_type)
            if not driver_class:
                raise DriverNotImplementedError(
                    f"Driver type '{outlet.driver_type}' is not supported"
                )
            
            # Instantiate driver with outlet configuration
            driver = driver_class(
                device_id=outlet.device_id,
                ip_address=outlet.ip_address,
                auth_info=outlet.auth_info
            )
            
            # Cache the driver instance
            self._active_drivers[outlet_id] = driver
            
            return driver
    
    async def turn_on_outlet(self, outlet_id: str) -> bool:
        """
        Turn on a smart outlet.
        
        Args:
            outlet_id: The ID of the outlet to turn on
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            OutletNotFoundError: If the outlet is not found
            DriverNotImplementedError: If the driver type is not supported
        """
        driver = await self._get_driver_instance(outlet_id)
        return await driver.turn_on()
    
    async def toggle_outlet(self, outlet_id: str) -> bool:
        """
        Toggle a smart outlet (turn off if on, turn on if off).
        
        Args:
            outlet_id: The ID of the outlet to toggle
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            OutletNotFoundError: If the outlet is not found
            DriverNotImplementedError: If the driver type is not supported
        """
        driver = await self._get_driver_instance(outlet_id)
        return await driver.toggle()
    
    async def get_outlet_status(self, outlet_id: str) -> SmartOutletState:
        """
        Get the current status of a smart outlet.
        
        Args:
            outlet_id: The ID of the outlet to get status for
            
        Returns:
            SmartOutletState: The current state of the outlet
            
        Raises:
            OutletNotFoundError: If the outlet is not found
            DriverNotImplementedError: If the driver type is not supported
        """
        driver = await self._get_driver_instance(outlet_id)
        return await driver.get_state() 