"""
Shelly SmartOutlet Driver

This module provides the ShellyDriver class for controlling Shelly Gen1/Gen2 devices
using the aioshelly library. Includes device discovery, control, and state retrieval.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any

import aioshelly
from aioshelly.exceptions import (
    DeviceConnectionError,
    DeviceConnectionTimeoutError,
    InvalidAuthError,
    ShellyError,  # Base exception for aioshelly errors
    # Add other exceptions if you specifically handle them, e.g., ConnectionClosed
)

from .base import AbstractSmartOutletDriver
from ..schemas import SmartOutletState
from ..exceptions import OutletConnectionError, OutletTimeoutError, OutletAuthenticationError


class ShellyDriver(AbstractSmartOutletDriver):
    """
    Driver for Shelly Gen1/Gen2 smart outlets.
    
    Supports both generations with automatic detection at runtime.
    Provides device discovery, control, and state retrieval.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the Shelly driver.
        
        Args:
            device_id (str): Unique identifier for the device
            ip_address (str): IP address of the Shelly device
            auth_info (Optional[Dict]): Optional authentication information (username/password)
        """
        super().__init__(device_id, ip_address, auth_info)
        self._logger = logging.getLogger(f"ShellyDriver.{device_id}")
    
    @classmethod
    async def discover_devices(cls) -> List[Dict[str, Any]]:
        """
        Discover Shelly devices on the local network.
        
        Returns:
            List[Dict]: List of discovered Shelly devices
        """
        logger = logging.getLogger("ShellyDriver.discovery")
        
        try:
            # Use aioshelly to discover devices
            discovered_devices = await aioshelly.discover()
            
            devices = []
            for device_info in discovered_devices:
                try:
                    # Extract device information
                    device_data = {
                        "driver_type": "shelly",
                        "driver_device_id": device_info.get('mac', f"shelly_{device_info.get('ip', 'unknown')}"),
                        "ip_address": device_info.get('ip'),
                        "name": device_info.get('name', f"Shelly Device {device_info.get('ip', 'unknown')}")
                    }
                    devices.append(device_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process discovered Shelly device: {e}")
                    continue
            
            logger.info(f"Discovered {len(devices)} Shelly devices")
            return devices
            
        except Exception as e:
            logger.error(f"Shelly discovery failed: {e}")
            return []
    
    async def _get_device(self) -> Any:
        """
        Create and initialize a device connection.
        
        Returns:
            Any: Connected device instance (aioshelly Device for Gen1 or Gen2)
        """
        device = aioshelly.Device(
            self.ip_address,
            username=self.auth_info.get('username'),
            password=self.auth_info.get('password')
        )
        
        await device.initialize()
        return device
    
    async def _get_relay(self, device: Any):
        """
        Get the relay component (Gen1) or switch component (Gen2).
        
        Args:
            device (Any): The aioshelly device instance
            
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
        async def _turn_on_action():
            device = None
            try:
                device = await self._get_device()
                relay = await self._get_relay(device)
                await relay.turn_on()
                return True
            except DeviceConnectionTimeoutError as e:
                self._logger.error(f"Timeout turning on Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout turning on outlet at {self.ip_address}: {e}")
            except InvalidAuthError as e:
                self._logger.error(f"Authentication error turning on Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error turning on outlet at {self.ip_address}: {e}")
            except DeviceConnectionError as e:
                self._logger.error(f"Connection error turning on Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error turning on outlet at {self.ip_address}: {e}")
            except ShellyError as e:
                self._logger.error(f"Shelly error turning on outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Shelly error turning on outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error turning on Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to turn on outlet at {self.ip_address}: {e}")
            finally:
                if device:
                    await device.shutdown()
        
        return await self._perform_network_action(_turn_on_action())
    
    async def _turn_off_implementation(self) -> bool:
        """
        Implementation of turn off operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        async def _turn_off_action():
            device = None
            try:
                device = await self._get_device()
                relay = await self._get_relay(device)
                await relay.turn_off()
                return True
            except DeviceConnectionTimeoutError as e:
                self._logger.error(f"Timeout turning off Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout turning off outlet at {self.ip_address}: {e}")
            except InvalidAuthError as e:
                self._logger.error(f"Authentication error turning off Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error turning off outlet at {self.ip_address}: {e}")
            except DeviceConnectionError as e:
                self._logger.error(f"Connection error turning off Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error turning off outlet at {self.ip_address}: {e}")
            except ShellyError as e:
                self._logger.error(f"Shelly error turning off outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Shelly error turning off outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error turning off Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to turn off outlet at {self.ip_address}: {e}")
            finally:
                if device:
                    await device.shutdown()
        
        return await self._perform_network_action(_turn_off_action())
    
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
        async def _get_state_action():
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
            except DeviceConnectionTimeoutError as e:
                self._logger.error(f"Timeout getting state for Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout getting state for outlet at {self.ip_address}: {e}")
            except InvalidAuthError as e:
                self._logger.error(f"Authentication error getting state for Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error getting state for outlet at {self.ip_address}: {e}")
            except DeviceConnectionError as e:
                self._logger.error(f"Connection error getting state for Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error getting state for outlet at {self.ip_address}: {e}")
            except ShellyError as e:
                self._logger.error(f"Shelly error getting state for outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Shelly error getting state for outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error getting state for Shelly outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to get state for outlet at {self.ip_address}: {e}")
            finally:
                if device:
                    await device.shutdown()
        
        return await self._perform_network_action(_get_state_action())
    
    async def discover_device(self) -> Dict:
        """
        Discover and return Shelly device information.
        
        Returns:
            Dict: Device information including generation, model, capabilities
        """
        async def _discover_action():
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
            except DeviceConnectionTimeoutError as e:
                self._logger.error(f"Timeout discovering Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout discovering device at {self.ip_address}: {e}")
            except InvalidAuthError as e:
                self._logger.error(f"Authentication error discovering Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error discovering device at {self.ip_address}: {e}")
            except DeviceConnectionError as e:
                self._logger.error(f"Connection error discovering Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error discovering device at {self.ip_address}: {e}")
            except ShellyError as e:
                self._logger.error(f"Shelly error discovering device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Shelly error discovering device at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error discovering Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to discover device at {self.ip_address}: {e}")
            finally:
                if device:
                    await device.shutdown()
        
        try:
            return await self._perform_network_action(_discover_action())
        except (OutletConnectionError, OutletTimeoutError, OutletAuthenticationError):
            # Return error info instead of re-raising for discovery
            return {
                'device_id': self.device_id,
                'ip_address': self.ip_address,
                'error': 'Device discovery failed'
            }
    
    async def get_energy_meter(self) -> Optional[Dict]:
        """
        Get energy meter data if available.
        
        Returns:
            Optional[Dict]: Energy data or None if not available
        """
        async def _get_energy_action():
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
            except DeviceConnectionTimeoutError as e:
                self._logger.error(f"Timeout getting energy meter for Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout getting energy meter for device at {self.ip_address}: {e}")
            except InvalidAuthError as e:
                self._logger.error(f"Authentication error getting energy meter for Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error getting energy meter for device at {self.ip_address}: {e}")
            except DeviceConnectionError as e:
                self._logger.error(f"Connection error getting energy meter for Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error getting energy meter for device at {self.ip_address}: {e}")
            except ShellyError as e:
                self._logger.error(f"Shelly error getting energy meter for device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Shelly error getting energy meter for device at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error getting energy meter for Shelly device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to get energy meter for device at {self.ip_address}: {e}")
            finally:
                if device:
                    await device.shutdown()
        
        try:
            return await self._perform_network_action(_get_energy_action())
        except (OutletConnectionError, OutletTimeoutError, OutletAuthenticationError):
            # Return None instead of re-raising for energy meter
            return None 