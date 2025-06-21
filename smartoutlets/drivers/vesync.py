"""
VeSync SmartOutlet Driver

This module provides the VeSyncDriver class for controlling VeSync devices
using the pyvesync library.
"""

import asyncio
import logging
from typing import Dict, Optional

from pyvesync import VeSync

from .base import AbstractSmartOutletDriver
from ..models import SmartOutletState


class VeSyncDriver(AbstractSmartOutletDriver):
    """
    Driver for VeSync smart outlets.
    
    Uses pyvesync library with asyncio.run_in_executor for non-blocking operations.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the VeSync driver.
        
        Args:
            device_id: Unique identifier for the device
            ip_address: IP address of the VeSync device
            auth_info: Authentication information containing email, password, and vesync_device_name
        """
        super().__init__(device_id, ip_address, auth_info)
        self._logger = logging.getLogger(f"VeSyncDriver.{device_id}")
        self._manager = None
        self._device = None
    
    async def _get_manager(self) -> VeSync:
        """
        Get or create the VeSync manager instance.
        
        Returns:
            VeSync: Authenticated manager instance
        """
        if self._manager is None:
            email = self.auth_info.get('email')
            password = self.auth_info.get('password')
            
            if not email or not password:
                raise ValueError("VeSync authentication requires email and password")
            
            self._manager = VeSync(email, password)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._manager.login)
            await loop.run_in_executor(None, self._manager.update)
        
        return self._manager
    
    async def _get_device(self):
        """
        Get the target VeSync device.
        
        Returns:
            VeSync device instance
        """
        if self._device is None:
            manager = await self._get_manager()
            loop = asyncio.get_running_loop()
            
            # Load outlets
            await loop.run_in_executor(None, manager.outlets)
            
            # Find target device by device_name or cid
            target_name = self.auth_info.get('vesync_device_name')
            target_cid = self.auth_info.get('cid')
            
            for outlet in manager.outlets:
                if (target_name and outlet.device_name == target_name) or \
                   (target_cid and outlet.cid == target_cid):
                    self._device = outlet
                    break
            
            if not self._device:
                raise ValueError(f"VeSync device not found: name={target_name}, cid={target_cid}")
        
        return self._device
    
    async def _turn_on_implementation(self) -> bool:
        """
        Implementation of turn on operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            device = await self._get_device()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, device.turn_on)
            return True
        except Exception as e:
            self._logger.error(f"Failed to turn on VeSync outlet {self.device_id}: {e}")
            return False
    
    async def _turn_off_implementation(self) -> bool:
        """
        Implementation of turn off operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            device = await self._get_device()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, device.turn_off)
            return True
        except Exception as e:
            self._logger.error(f"Failed to turn off VeSync outlet {self.device_id}: {e}")
            return False
    
    async def _toggle_implementation(self) -> bool:
        """
        Implementation of toggle operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        current_state = await self._get_state_implementation()
        if current_state.is_on:
            return await self._turn_off_implementation()
        else:
            return await self._turn_on_implementation()
    
    async def _get_state_implementation(self) -> SmartOutletState:
        """
        Implementation of get state operation.
        
        Returns:
            SmartOutletState: Current state information
        """
        try:
            device = await self._get_device()
            loop = asyncio.get_running_loop()
            
            # Update device state
            await loop.run_in_executor(None, device.update)
            
            # Get basic state
            is_on = device.is_on
            
            # Get power usage if available
            power_w = None
            try:
                power_data = await loop.run_in_executor(None, device.get_power_usage)
                if power_data:
                    power_w = power_data.get('power')
            except Exception as e:
                # Power usage not available
                self._logger.debug(f"Power usage not available for {self.device_id}: {e}")
            
            return SmartOutletState(
                is_on=is_on,
                power_w=power_w
            )
        except Exception as e:
            self._logger.error(f"Failed to get state for VeSync outlet {self.device_id}: {e}")
            return SmartOutletState(is_on=False)
    
    async def discover_device(self) -> Dict:
        """
        Discover and return VeSync device information.
        
        Returns:
            Dict: Device information including model, capabilities, etc.
        """
        try:
            device = await self._get_device()
            loop = asyncio.get_running_loop()
            
            # Update device info
            await loop.run_in_executor(None, device.update)
            
            return {
                'device_id': self.device_id,
                'ip_address': self.ip_address,
                'device_name': device.device_name,
                'model': device.device_type,
                'cid': device.cid,
                'uuid': device.uuid,
                'is_on': device.is_on,
                'status': 'connected'
            }
        except Exception as e:
            self._logger.error(f"Failed to discover VeSync device {self.device_id}: {e}")
            return {
                'device_id': self.device_id,
                'ip_address': self.ip_address,
                'error': str(e)
            }
    
    async def get_energy_meter(self) -> Optional[Dict]:
        """
        Get energy meter data if available.
        
        Returns:
            Optional[Dict]: Energy data or None if not available
        """
        try:
            device = await self._get_device()
            loop = asyncio.get_running_loop()
            
            # Get power usage data
            power_data = await loop.run_in_executor(None, device.get_power_usage)
            
            if not power_data:
                return None
            
            energy_data = {
                'power_w': power_data.get('power'),
                'voltage_v': power_data.get('voltage'),
                'current_a': power_data.get('current'),
                'energy_kwh': power_data.get('energy'),
                'timestamp': power_data.get('timestamp')
            }
            
            # Filter out None values
            energy_data = {k: v for k, v in energy_data.items() if v is not None}
            
            return energy_data if energy_data else None
        except Exception as e:
            self._logger.error(f"Failed to get energy meter data for VeSync outlet {self.device_id}: {e}")
            return None 