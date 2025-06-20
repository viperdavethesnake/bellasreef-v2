"""
VeSync SmartOutlet Driver

This module provides the VeSyncDriver class for controlling VeSync devices
using the pyvesync library v2.1.18. Includes device discovery, control, and state retrieval.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any

from pyvesync import VeSync
import requests

from .base import AbstractSmartOutletDriver
from ..models import SmartOutletState
from ..exceptions import OutletConnectionError, OutletTimeoutError, OutletAuthenticationError


class VeSyncDriver(AbstractSmartOutletDriver):
    """
    Driver for VeSync smart outlets.
    
    Uses pyvesync library v2.1.18 with asyncio.run_in_executor for non-blocking operations.
    Supports device discovery, control, and state retrieval.
    """
    
    def __init__(self, device_id: str, ip_address: str, auth_info: Optional[Dict] = None):
        """
        Initialize the VeSync driver.
        
        Args:
            device_id (str): Unique identifier for the device
            ip_address (str): IP address of the VeSync device
            auth_info (Optional[Dict]): Authentication information containing email, password, and vesync_device_name
        """
        super().__init__(device_id, ip_address, auth_info)
        self._logger = logging.getLogger(f"VeSyncDriver.{device_id}")
        self._manager = None
        self._device = None
    
    @classmethod
    async def discover_devices(cls, email: str, password: str) -> List[Dict[str, Any]]:
        """
        Discover VeSync devices using cloud credentials.
        
        Args:
            email (str): VeSync account email
            password (str): VeSync account password
            
        Returns:
            List[Dict]: List of discovered VeSync devices
            
        Raises:
            OutletAuthenticationError: If credentials are invalid
            OutletConnectionError: If discovery fails
        """
        logger = logging.getLogger("VeSyncDriver.discovery")
        
        try:
            loop = asyncio.get_running_loop()
            
            # Create VeSync manager and login
            manager = VeSync(email, password)
            login_success = await loop.run_in_executor(None, manager.login)
            
            if not login_success:
                raise OutletAuthenticationError(f"VeSync authentication failed for {email}")
            
            # Update to populate devices - outlets are available in manager.outlets after this
            await loop.run_in_executor(None, manager.update)
            
            devices = []
            for outlet in manager.outlets:
                try:
                    # Extract device information
                    device_data = {
                        "driver_type": "vesync",
                        "driver_device_id": outlet.cid,  # CID as driver_device_id
                        "ip_address": None,  # No IP address for cloud devices
                        "name": outlet.device_name
                    }
                    devices.append(device_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process discovered VeSync device: {e}")
                    continue
            
            logger.info(f"Discovered {len(devices)} VeSync devices")
            return devices
            
        except requests.exceptions.Timeout as e:
            logger.error(f"VeSync discovery timeout: {e}")
            raise OutletTimeoutError(f"VeSync discovery timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"VeSync discovery connection error: {e}")
            raise OutletConnectionError(f"VeSync discovery connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"VeSync discovery request error: {e}")
            raise OutletConnectionError(f"VeSync discovery request error: {e}")
        except OutletAuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error during VeSync discovery: {e}")
            raise OutletConnectionError(f"VeSync discovery failed: {e}")
    
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
            
            loop = asyncio.get_running_loop()
            
            # Create manager instance
            self._manager = VeSync(email, password)
            
            # Login and check result
            login_success = await loop.run_in_executor(None, self._manager.login)
            if not login_success:
                raise OutletAuthenticationError(f"VeSync authentication failed for {email}")
            
            # Update device list
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
        async def _turn_on_action():
            try:
                device = await self._get_device()
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, device.turn_on)
                return True
            except requests.exceptions.Timeout as e:
                self._logger.error(f"Timeout turning on VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout turning on outlet at {self.ip_address}: {e}")
            except requests.exceptions.ConnectionError as e:
                self._logger.error(f"Connection error turning on VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error turning on outlet at {self.ip_address}: {e}")
            except requests.exceptions.RequestException as e:
                self._logger.error(f"Request error turning on VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Request error turning on outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error turning on VeSync outlet {self.device_id} at {self.ip_address}: {e}")
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
                device = await self._get_device()
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, device.turn_off)
                return True
            except requests.exceptions.Timeout as e:
                self._logger.error(f"Timeout turning off VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout turning off outlet at {self.ip_address}: {e}")
            except requests.exceptions.ConnectionError as e:
                self._logger.error(f"Connection error turning off VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error turning off outlet at {self.ip_address}: {e}")
            except requests.exceptions.RequestException as e:
                self._logger.error(f"Request error turning off VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Request error turning off outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error turning off VeSync outlet {self.device_id} at {self.ip_address}: {e}")
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
                except AttributeError:
                    # Power usage not available for this device
                    self._logger.debug(f"Power usage not available for {self.device_id} at {self.ip_address}")
                except Exception as e:
                    # Power usage not available or failed
                    self._logger.debug(f"Power usage not available for {self.device_id} at {self.ip_address}: {e}")
                
                return SmartOutletState(
                    is_on=is_on,
                    power_w=power_w
                )
            except requests.exceptions.Timeout as e:
                self._logger.error(f"Timeout getting state for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout getting state for outlet at {self.ip_address}: {e}")
            except requests.exceptions.ConnectionError as e:
                self._logger.error(f"Connection error getting state for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error getting state for outlet at {self.ip_address}: {e}")
            except requests.exceptions.RequestException as e:
                self._logger.error(f"Request error getting state for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Request error getting state for outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error getting state for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to get state for outlet at {self.ip_address}: {e}")
        
        return await self._perform_network_action(_get_state_action())
    
    async def discover_device(self) -> Dict:
        """
        Discover and return VeSync device information.
        
        Returns:
            Dict: Device information including model, capabilities, etc.
        """
        async def _discover_action():
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
            except requests.exceptions.Timeout as e:
                self._logger.error(f"Timeout discovering VeSync device {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout discovering device at {self.ip_address}: {e}")
            except requests.exceptions.ConnectionError as e:
                self._logger.error(f"Connection error discovering VeSync device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error discovering device at {self.ip_address}: {e}")
            except requests.exceptions.RequestException as e:
                self._logger.error(f"Request error discovering VeSync device {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Request error discovering device at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error discovering VeSync device {self.device_id} at {self.ip_address}: {e}")
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
            except AttributeError:
                # Energy meter not available for this device
                self._logger.debug(f"Energy meter not available for {self.device_id} at {self.ip_address}")
                return None
            except requests.exceptions.Timeout as e:
                self._logger.error(f"Timeout getting energy meter for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletTimeoutError(f"Timeout getting energy meter for outlet at {self.ip_address}: {e}")
            except requests.exceptions.ConnectionError as e:
                self._logger.error(f"Connection error getting energy meter for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Connection error getting energy meter for outlet at {self.ip_address}: {e}")
            except requests.exceptions.RequestException as e:
                self._logger.error(f"Request error getting energy meter for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Request error getting energy meter for outlet at {self.ip_address}: {e}")
            except Exception as e:
                self._logger.error(f"Unexpected error getting energy meter for VeSync outlet {self.device_id} at {self.ip_address}: {e}")
                raise OutletConnectionError(f"Failed to get energy meter for outlet at {self.ip_address}: {e}")
        
        try:
            return await self._perform_network_action(_get_energy_action())
        except (OutletConnectionError, OutletTimeoutError, OutletAuthenticationError):
            # Return None instead of re-raising for energy meter
            return None 