"""
Kasa SmartOutlet Driver

This module provides the KasaDriver class for controlling TP-Link Kasa devices
using the pyHS100 library.
"""

import asyncio
import logging
from typing import Dict, Optional

from pyHS100 import SmartPlug

from .base import AbstractSmartOutletDriver
from ..models import SmartOutletState


class KasaDriver(AbstractSmartOutletDriver):
    """
    Driver for TP-Link Kasa smart outlets.
    
    Uses pyHS100 library with asyncio.run_in_executor for non-blocking operations.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the Kasa driver.
        
        Args:
            device_id: Unique identifier for the device
            ip_address: IP address of the Kasa device
            auth_info: Optional authentication information
        """
        super().__init__(device_id, ip_address, auth_info)
        self._logger = logging.getLogger(f"KasaDriver.{device_id}")
    
    async def turn_on(self) -> bool:
        """
        Turn on the Kasa outlet.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            plug = SmartPlug(self.ip_address)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, plug.turn_on)
            return True
        except Exception as e:
            self._logger.error(f"Failed to turn on Kasa outlet {self.device_id}: {e}")
            return False
    
    async def turn_off(self) -> bool:
        """
        Turn off the Kasa outlet.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            plug = SmartPlug(self.ip_address)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, plug.turn_off)
            return True
        except Exception as e:
            self._logger.error(f"Failed to turn off Kasa outlet {self.device_id}: {e}")
            return False
    
    async def toggle(self) -> bool:
        """
        Toggle the Kasa outlet state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        current_state = await self.get_state()
        if current_state.is_on:
            return await self.turn_off()
        else:
            return await self.turn_on()
    
    async def get_state(self) -> SmartOutletState:
        """
        Get the current state of the Kasa outlet.
        
        Returns:
            SmartOutletState: Current state information
        """
        try:
            plug = SmartPlug(self.ip_address)
            loop = asyncio.get_running_loop()
            
            # Get basic state
            state = await loop.run_in_executor(None, lambda: plug.state)
            is_on = state == "ON"
            
            # Get energy meter data if available
            power_w = None
            current_ma = None
            voltage_v = None
            
            try:
                emeter_data = await loop.run_in_executor(None, plug.get_emeter_realtime)
                if emeter_data:
                    power_w = emeter_data.get('power')
                    current_ma = emeter_data.get('current')
                    voltage_v = emeter_data.get('voltage')
            except Exception as e:
                # Energy meter not available or failed
                self._logger.debug(f"Energy meter not available for {self.device_id}: {e}")
            
            return SmartOutletState(
                is_on=is_on,
                power_w=power_w,
                voltage_v=voltage_v,
                current_a=current_ma / 1000.0 if current_ma is not None else None
            )
        except Exception as e:
            self._logger.error(f"Failed to get state for Kasa outlet {self.device_id}: {e}")
            return SmartOutletState(is_on=False)
    
    async def discover_device(self) -> Dict:
        """
        Discover and return Kasa device information.
        
        Returns:
            Dict: Device information including model, hardware version, etc.
        """
        try:
            plug = SmartPlug(self.ip_address)
            loop = asyncio.get_running_loop()
            
            # Get device information
            info = await loop.run_in_executor(None, plug.get_sysinfo)
            
            return {
                'device_id': self.device_id,
                'ip_address': self.ip_address,
                'alias': info.get('alias', 'Unknown'),
                'model': info.get('model', 'Unknown'),
                'hw_version': info.get('hw_ver', 'Unknown'),
                'sw_version': info.get('sw_ver', 'Unknown'),
                'mac': info.get('mac', 'Unknown'),
                'device_id_kasa': info.get('deviceId', 'Unknown'),
                'status': 'connected'
            }
        except Exception as e:
            self._logger.error(f"Failed to discover Kasa device {self.device_id}: {e}")
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
            plug = SmartPlug(self.ip_address)
            loop = asyncio.get_running_loop()
            emeter_data = await loop.run_in_executor(None, plug.get_emeter_realtime)
            
            if not emeter_data:
                return None
            
            # Convert current from mA to A
            current_a = None
            if emeter_data.get('current') is not None:
                current_a = emeter_data['current'] / 1000.0
            
            energy_data = {
                'power_w': emeter_data.get('power'),
                'voltage_v': emeter_data.get('voltage'),
                'current_a': current_a,
                'total_wh': emeter_data.get('total'),
                'timestamp': emeter_data.get('timestamp')
            }
            
            # Filter out None values
            energy_data = {k: v for k, v in energy_data.items() if v is not None}
            
            return energy_data if energy_data else None
        except Exception as e:
            self._logger.error(f"Failed to get energy meter data for Kasa outlet {self.device_id}: {e}")
            return None 