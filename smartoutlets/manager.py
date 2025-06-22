"""
SmartOutlet Manager Module

This module provides the main SmartOutletManager class that handles outlet operations
with support for multiple driver types (Kasa, Shelly, VeSync).
"""

import logging
from typing import Callable, Dict, Type, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.core.config import settings, is_driver_enabled
from .drivers import AbstractSmartOutletDriver, KasaDriver, ShellyDriver, VeSyncDriver
from .exceptions import DriverNotImplementedError, OutletNotFoundError, OutletConnectionError
from shared.db.models import SmartOutlet
from .schemas import SmartOutletState, SmartOutletUpdate, SmartOutletRead


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
        if not settings.SMART_OUTLETS_ENABLED:
            raise RuntimeError("SmartOutlets module is disabled via config.")
    
    async def get_all_outlets(self, include_disabled: bool = False) -> List[SmartOutlet]:
        """
        Get all outlets from the database.
        
        Args:
            include_disabled: Whether to include disabled outlets
            
        Returns:
            List[SmartOutlet]: List of outlet instances
        """
        async with self._db_session_factory() as session:
            query = select(SmartOutlet)
            if not include_disabled:
                query = query.where(SmartOutlet.enabled == True)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def update_outlet(self, outlet_id: str, update_data: SmartOutletUpdate) -> SmartOutletRead:
        """
        Update an existing outlet configuration.
        
        Args:
            outlet_id: The ID of the outlet to update
            update_data: Update data containing allowed fields
            
        Returns:
            SmartOutletRead: Updated outlet data
            
        Raises:
            OutletNotFoundError: If the outlet is not found
        """
        async with self._db_session_factory() as session:
            outlet = await session.get(SmartOutlet, outlet_id)
            
            if not outlet:
                raise OutletNotFoundError(f"Outlet with ID {outlet_id} not found")
            
            # Update allowed fields
            if update_data.nickname is not None:
                outlet.nickname = update_data.nickname
                self._logger.info(f"Updated nickname for outlet {outlet_id} to '{update_data.nickname}'")
            
            if update_data.location is not None:
                outlet.location = update_data.location
                self._logger.info(f"Updated location for outlet {outlet_id} to '{update_data.location}'")
            
            if update_data.role is not None:
                outlet.role = update_data.role.value
                self._logger.info(f"Updated role for outlet {outlet_id} to '{update_data.role.value}'")
            
            if update_data.enabled is not None:
                old_enabled = outlet.enabled
                outlet.enabled = update_data.enabled
                
                if old_enabled and not update_data.enabled:
                    # Outlet was disabled, remove from cache
                    if outlet_id in self._active_drivers:
                        try:
                            del self._active_drivers[outlet_id]
                            self._logger.info(f"Removed disabled outlet {outlet_id} from driver cache")
                        except Exception as e:
                            self._logger.warning(f"Failed to remove outlet {outlet_id} from cache: {e}")
                
                self._logger.info(f"Updated enabled status for outlet {outlet_id} to {update_data.enabled}")
            
            await session.commit()
            await session.refresh(outlet)
            
            return SmartOutletRead.model_validate(outlet)
    
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
            if not is_driver_enabled(outlet.driver_type):
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
                device_id=outlet.driver_device_id,
                ip_address=outlet.ip_address,
                auth_info=outlet.auth_info
            )
            
            # Cache the driver instance
            self._active_drivers[outlet_id] = driver
            
            return driver
    
    async def register_outlet_from_db(self, outlet_id: str) -> None:
        """
        Register an outlet from the database with the manager.
        
        Args:
            outlet_id: The ID of the outlet to register
            
        Raises:
            OutletNotFoundError: If the outlet is not found
            DriverNotImplementedError: If the driver type is not supported
        """
        # This will validate the outlet exists and create the driver instance
        await self._get_driver_instance(outlet_id)
    
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
            OutletConnectionError: If the outlet is unreachable
        """
        try:
            driver = await self._get_driver_instance(outlet_id)
            success = await driver.turn_on()
            
            if success:
                self._logger.info(f"Successfully turned on outlet {outlet_id}")
            else:
                self._logger.warning(f"Failed to turn on outlet {outlet_id}")
            
            return success
        except (OutletNotFoundError, DriverNotImplementedError):
            raise
        except Exception as e:
            self._logger.error(f"Connection error turning on outlet {outlet_id}: {e}")
            raise OutletConnectionError(f"Failed to connect to outlet {outlet_id}: {e}")
    
    async def turn_off_outlet(self, outlet_id: str) -> bool:
        """
        Turn off a smart outlet.
        
        Args:
            outlet_id: The ID of the outlet to turn off
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            OutletNotFoundError: If the outlet is not found
            DriverNotImplementedError: If the driver type is not supported
            OutletConnectionError: If the outlet is unreachable
        """
        try:
            driver = await self._get_driver_instance(outlet_id)
            success = await driver.turn_off()
            
            if success:
                self._logger.info(f"Successfully turned off outlet {outlet_id}")
            else:
                self._logger.warning(f"Failed to turn off outlet {outlet_id}")
            
            return success
        except (OutletNotFoundError, DriverNotImplementedError):
            raise
        except Exception as e:
            self._logger.error(f"Connection error turning off outlet {outlet_id}: {e}")
            raise OutletConnectionError(f"Failed to connect to outlet {outlet_id}: {e}")
    
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
            OutletConnectionError: If the outlet is unreachable
        """
        try:
            driver = await self._get_driver_instance(outlet_id)
            success = await driver.toggle()
            
            if success:
                self._logger.info(f"Successfully toggled outlet {outlet_id}")
            else:
                self._logger.warning(f"Failed to toggle outlet {outlet_id}")
            
            return success
        except (OutletNotFoundError, DriverNotImplementedError):
            raise
        except Exception as e:
            self._logger.error(f"Connection error toggling outlet {outlet_id}: {e}")
            raise OutletConnectionError(f"Failed to connect to outlet {outlet_id}: {e}")
    
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
            OutletConnectionError: If the outlet is unreachable
        """
        try:
            driver = await self._get_driver_instance(outlet_id)
            raw_state = await driver.get_state()
            
            # Convert dataclass to Pydantic schema
            state = SmartOutletState(
                is_on=raw_state.is_on,
                power_w=raw_state.power_w,
                voltage_v=raw_state.voltage_v,
                current_a=raw_state.current_a,
                energy_kwh=raw_state.energy_kwh,
                temperature_c=raw_state.temperature_c,
                is_online=True  # If we got a response, the outlet is online
            )
            
            self._logger.debug(f"Retrieved state for outlet {outlet_id}: {state}")
            return state
        except (OutletNotFoundError, DriverNotImplementedError):
            raise
        except Exception as e:
            self._logger.error(f"Connection error getting state for outlet {outlet_id}: {e}")
            raise OutletConnectionError(f"Failed to connect to outlet {outlet_id}: {e}") 