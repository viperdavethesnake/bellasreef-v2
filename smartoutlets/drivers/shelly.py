"""
Shelly SmartOutlet Driver

This module provides the ShellyDriver class for controlling Shelly Gen1/Gen2 devices
using the aioshelly library.
"""

import logging
from typing import Dict, Optional

import aioshelly

from .base import AbstractSmartOutletDriver
from ..models import SmartOutletState


class ShellyDriver(AbstractSmartOutletDriver):
    """
    Driver for Shelly Gen1/Gen2 smart outlets.
    
    Supports both generations with automatic detection at runtime.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the Shelly driver.
        
        Args:
            device_id: Unique identifier for the device
            ip_address: IP address of the Shelly device
            auth_info: Optional authentication information (username/password)
        """
        super().__init__(device_id, ip_address, auth_info)
        self._logger = logging.getLogger(f"ShellyDriver.{device_id}")
    
    async def _get_device(self) -> aioshelly.Device:
        """
        Create and initialize a device connection.
        
        Returns:
            aioshelly.Device: Connected device instance
        """
        device = aioshelly.Device(
            self.ip_address,
            username=self.auth_info.get('username'),
            password=self.auth_info.get('password')
        )
        
        await device.initialize()
        return device
    
    async def _get_relay(self, device: aioshelly.Device):
        """
        Get the relay component (Gen1) or switch component (Gen2).
        
        Args:
            device: The aioshelly device instance
            
        Returns:
            Relay or Switch component
        """
        if device.gen == 2:
            return device.switch[0]
        else:
            return device.relay[0]
    
    async def _turn_on_implementation(self) -> bool:
        """
        Implementation of turn on operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        device = None
        try:
            device = await self._get_device()
            relay = await self._get_relay(device)
            await relay.turn_on()
            return True
        except Exception as e:
            self._logger.error(f"Failed to turn on Shelly outlet {self.device_id}: {e}")
            return False
        finally:
            if device:
                await device.shutdown()
    
    async def _turn_off_implementation(self) -> bool:
        """
        Implementation of turn off operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        device = None
        try:
            device = await self._get_device()
            relay = await self._get_relay(device)
            await relay.turn_off()
            return True
        except Exception as e:
            self._logger.error(f"Failed to turn off Shelly outlet {self.device_id}: {e}")
            return False
        finally:
            if device:
                await device.shutdown()
    
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
        device = None
        try:
            device = await self._get_device()
            relay = await self._get_relay(device)
            
            # Get basic state
            is_on = relay.output
            
            # Get power information if available
            power_w = None
            if device.gen == 2:
                # Gen2 has apower (active power)
                power_w = getattr(relay, 'apower', None)
            else:
                # Gen1 has power
                power_w = getattr(relay, 'power', None)
            
            return SmartOutletState(
                is_on=is_on,
                power_w=power_w
            )
        except Exception as e:
            self._logger.error(f"Failed to get state for Shelly outlet {self.device_id}: {e}")
            return SmartOutletState(is_on=False)
        finally:
            if device:
                await device.shutdown()
    
    async def discover_device(self) -> Dict:
        """
        Discover and return Shelly device information.
        
        Returns:
            Dict: Device information including generation, model, capabilities
        """
        device = None
        try:
            device = await self._get_device()
            
            info = {
                'device_id': self.device_id,
                'ip_address': self.ip_address,
                'model': device.model,
                'generation': device.gen,
                'firmware': device.firmware,
                'mac': device.mac,
                'components': list(device.shelly.keys())
            }
            
            # Add relay/switch info
            relay = await self._get_relay(device)
            info['relay_type'] = 'switch' if device.gen == 2 else 'relay'
            info['relay_output'] = relay.output
            
            return info
        except Exception as e:
            self._logger.error(f"Failed to discover Shelly device {self.device_id}: {e}")
            return {
                'device_id': self.device_id,
                'ip_address': self.ip_address,
                'error': str(e)
            }
        finally:
            if device:
                await device.shutdown()
    
    async def get_energy_meter(self) -> Optional[Dict]:
        """
        Get energy meter data if available.
        
        Returns:
            Optional[Dict]: Energy data or None if not available
        """
        device = None
        try:
            device = await self._get_device()
            
            if device.gen == 2:
                # Gen2 energy meter
                if hasattr(device, 'emeter') and device.emeter:
                    emeter = device.emeter[0]
                    return {
                        'power_w': getattr(emeter, 'apower', None),
                        'voltage_v': getattr(emeter, 'voltage', None),
                        'current_a': getattr(emeter, 'current', None),
                        'energy_kwh': getattr(emeter, 'aenergy', {}).get('total', None)
                    }
            else:
                # Gen1 energy meter
                if hasattr(device, 'emeter') and device.emeter:
                    emeter = device.emeter[0]
                    return {
                        'power_w': getattr(emeter, 'power', None),
                        'voltage_v': getattr(emeter, 'voltage', None),
                        'current_a': getattr(emeter, 'current', None),
                        'energy_kwh': getattr(emeter, 'total', None)
                    }
            
            return None
        except Exception as e:
            self._logger.error(f"Failed to get energy meter for Shelly device {self.device_id}: {e}")
            return None
        finally:
            if device:
                await device.shutdown() 