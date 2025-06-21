"""
Kasa SmartOutlet Driver

This module provides the KasaDriver class for controlling TP-Link Kasa devices
using the python-kasa library. Includes device discovery, control, and state retrieval.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any

import kasa
from kasa import SmartPlug, Discover
from kasa.exceptions import (
    AuthenticationError,
    DeviceError,
    TimeoutError,
    KasaException,
    UnsupportedDeviceError
)

from .base import AbstractSmartOutletDriver
from ..models import SmartOutletState
from ..exceptions import OutletConnectionError, OutletTimeoutError, OutletAuthenticationError


class KasaDriver(AbstractSmartOutletDriver):
    """
    Driver for TP-Link Kasa smart outlets.
    
    Uses python-kasa library with full async support.
    Supports device discovery, control, and state retrieval.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the Kasa driver.
        
        Args:
            device_id (str): Unique identifier for the device
            ip_address (str): IP address of the Kasa device
            auth_info (Optional[Dict]): Optional authentication information
        """
        super().__init__(device_id, ip_address, auth_info)
        self._logger = logging.getLogger(f"KasaDriver.{device_id}")
    
    @classmethod
    async def discover_devices(cls) -> List[Dict[str, Any]]:
        """
        Discover Kasa devices on the local network.
        
        Returns:
            List[Dict]: List of discovered Kasa devices
        """
        logger = logging.getLogger("KasaDriver.discovery")
        
        try:
            # Use python-kasa async discovery
            discovered_devices = await Discover.discover()
            
            devices = []
            for ip_address, device in discovered_devices.items():
                try:
                    # Extract device information
                    device_data = {
                        "driver_type": "kasa",
                        "driver_device_id": device.device_id if hasattr(device, 'device_id') else f"kasa_{ip_address}",
                        "ip_address": ip_address,
                        "name": device.alias if hasattr(device, 'alias') else f"Kasa Device {ip_address}"
                    }
                    devices.append(device_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process discovered Kasa device at {ip_address}: {e}")
                    continue
            
            logger.info(f"Discovered {len(devices)} Kasa devices")
            return devices
            
        except Exception as e:
            logger.error(f"Kasa discovery failed: {e}")
            return []
    
    async def _create_smart_plug(self) -> SmartPlug:
        """
        Create a fresh SmartPlug instance.
        
        Returns:
            SmartPlug: New SmartPlug instance
        """
        return SmartPlug(self.ip_address)
    
    async def _turn_on_implementation(self) -> bool:
        """
        Implementation of turn on operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        async def _turn_on_action():
            try:
                plug = await self._create_smart_plug()
                await plug.turn_on()
                return True
            except TimeoutError as e:
                self._logger.error(f"Timeout turning on Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout turning on outlet at {self.ip_address}: {e}")
            except AuthenticationError as e:
                self._logger.error(f"Authentication error turning on Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error turning on outlet at {self.ip_address}: {e}")
            except DeviceError as e:
                self._logger.error(f"Device error turning on Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Device error turning on outlet at {self.ip_address}: {e}")
            except KasaException as e:
                self._logger.error(f"Kasa error turning on outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Kasa error turning on outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error turning on Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to turn on outlet at {self.ip_address}: {e}")
        
        return await self._perform_network_action(_turn_on_action())
    
    async def _turn_off_implementation(self) -> bool:
        """
        Implementation of turn off operation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        async def _turn_off_action():
            try:
                plug = await self._create_smart_plug()
                await plug.turn_off()
                return True
            except TimeoutError as e:
                self._logger.error(f"Timeout turning off Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout turning off outlet at {self.ip_address}: {e}")
            except AuthenticationError as e:
                self._logger.error(f"Authentication error turning off Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error turning off outlet at {self.ip_address}: {e}")
            except DeviceError as e:
                self._logger.error(f"Device error turning off Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Device error turning off outlet at {self.ip_address}: {e}")
            except KasaException as e:
                self._logger.error(f"Kasa error turning off outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Kasa error turning off outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error turning off Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to turn off outlet at {self.ip_address}: {e}")
        
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
            try:
                plug = await self._create_smart_plug()
                
                # Always update device state before querying
                await plug.update()
                
                # Get basic state
                is_on = plug.is_on
                
                # Get energy meter data if available
                power_w = None
                current_a = None
                voltage_v = None
                
                try:
                    if hasattr(plug, 'emeter_realtime'):
                        emeter_data = plug.emeter_realtime
                        if emeter_data:
                            power_w = emeter_data.get('power')
                            current_ma = emeter_data.get('current')
                            voltage_v = emeter_data.get('voltage')
                            current_a = current_ma / 1000.0 if current_ma is not None else None
                except Exception as e:
                    # Energy meter not available or failed
                    self._logger.debug(f"Energy meter not available for {self.device_id} at {self.ip_address}: {e}")
                
                return SmartOutletState(
                    is_on=is_on,
                    power_w=power_w,
                    voltage_v=voltage_v,
                    current_a=current_a
                )
            except TimeoutError as e:
                self._logger.error(f"Timeout getting state for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout getting state for outlet at {self.ip_address}: {e}")
            except AuthenticationError as e:
                self._logger.error(f"Authentication error getting state for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error getting state for outlet at {self.ip_address}: {e}")
            except DeviceError as e:
                self._logger.error(f"Device error getting state for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Device error getting state for outlet at {self.ip_address}: {e}")
            except KasaException as e:
                self._logger.error(f"Kasa error getting state for outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Kasa error getting state for outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error getting state for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to get state for outlet at {self.ip_address}: {e}")
        
        return await self._perform_network_action(_get_state_action())
    
    async def discover_device(self) -> Dict:
        """
        Discover and return Kasa device information.
        
        Returns:
            Dict: Device information including model, hardware version, etc.
        """
        async def _discover_action():
            try:
                plug = await self._create_smart_plug()
                
                # Get device information
                await plug.update()
                info = plug.sys_info
                
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
            except TimeoutError as e:
                self._logger.error(f"Timeout discovering Kasa device {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout discovering device at {self.ip_address}: {e}")
            except AuthenticationError as e:
                self._logger.error(f"Authentication error discovering Kasa device {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error discovering device at {self.ip_address}: {e}")
            except DeviceError as e:
                self._logger.error(f"Device error discovering Kasa device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Device error discovering device at {self.ip_address}: {e}")
            except KasaException as e:
                self._logger.error(f"Kasa error discovering device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Kasa error discovering device at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error discovering Kasa device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to discover device at {self.ip_address}: {e}")
        
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
            try:
                plug = await self._create_smart_plug()
                await plug.update()
                
                if not hasattr(plug, 'emeter_realtime'):
                    return None
                
                emeter_data = plug.emeter_realtime
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
            except TimeoutError as e:
                self._logger.error(f"Timeout getting energy meter for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout getting energy meter for outlet at {self.ip_address}: {e}")
            except AuthenticationError as e:
                self._logger.error(f"Authentication error getting energy meter for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletAuthenticationError(f"Authentication error getting energy meter for outlet at {self.ip_address}: {e}")
            except DeviceError as e:
                self._logger.error(f"Device error getting energy meter for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Device error getting energy meter for outlet at {self.ip_address}: {e}")
            except KasaException as e:
                self._logger.error(f"Kasa error getting energy meter for outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Kasa error getting energy meter for outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error getting energy meter for Kasa outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to get energy meter for outlet at {self.ip_address}: {e}")
        
        try:
            return await self._perform_network_action(_get_energy_action())
        except (OutletConnectionError, OutletTimeoutError, OutletAuthenticationError):
            # Return None instead of re-raising for energy meter
            return None 