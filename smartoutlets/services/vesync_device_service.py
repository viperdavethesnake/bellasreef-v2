"""
VeSync Device Service

This module provides services for managing VeSync smart outlet devices,
including discovery, state management, and control operations.
"""

import asyncio
from typing import List, Optional, Dict, Any
from pyvesync import VeSync

from shared.utils.logger import get_logger
from ..crypto_utils import decrypt_vesync_password
from ..models import VeSyncAccount, SmartOutlet
from ..schemas import DiscoveredVeSyncDevice, SmartOutletWithState
from ..exceptions import OutletAuthenticationError, OutletConnectionError


logger = get_logger(__name__)


class VeSyncDeviceService:
    """
    Service for managing VeSync smart outlet devices.
    
    Handles cloud API interactions, device discovery, state management,
    and control operations using stored account credentials.
    """
    
    def __init__(self):
        """Initialize the VeSync device service."""
        self._managers: Dict[int, VeSync] = {}
    
    async def _get_manager(self, account: VeSyncAccount) -> VeSync:
        """
        Get or create a VeSync manager for the account.
        
        Args:
            account: VeSync account with encrypted credentials
            
        Returns:
            VeSync: Configured VeSync manager instance
            
        Raises:
            OutletAuthenticationError: If credentials are invalid
        """
        if account.id in self._managers:
            return self._managers[account.id]
        
        # Decrypt password
        password = decrypt_vesync_password(account.password_encrypted.decode())
        if not password:
            raise OutletAuthenticationError(f"Could not decrypt password for account {account.email}")
        
        # Create manager with stored timezone
        manager = VeSync(account.email, password, time_zone=account.time_zone)
        
        # Login
        login_success = await asyncio.to_thread(manager.login)
        if not login_success:
            error_msg = manager.error_msg or "Unknown login error"
            raise OutletAuthenticationError(f"VeSync login failed for {account.email}: {error_msg}")
        
        # Store manager for reuse
        self._managers[account.id] = manager
        return manager
    
    async def discover_devices(self, account: VeSyncAccount) -> List[DiscoveredVeSyncDevice]:
        """
        Discover all devices available for the VeSync account.
        
        Args:
            account: VeSync account to discover devices for
            
        Returns:
            List[DiscoveredVeSyncDevice]: List of discovered devices
            
        Raises:
            OutletAuthenticationError: If credentials are invalid
            OutletConnectionError: If discovery fails
        """
        try:
            manager = await self._get_manager(account)
            
            # Get all devices from VeSync
            devices = []
            
            # Get outlets
            if hasattr(manager, 'outlets') and manager.outlets:
                for outlet in manager.outlets:
                    devices.append(DiscoveredVeSyncDevice(
                        vesync_device_id=outlet.cid,
                        device_name=outlet.device_name,
                        device_type="outlet",
                        model=outlet.device_type,
                        is_online=outlet.is_online,
                        is_on=outlet.is_on,
                        power_w=getattr(outlet, 'power', None)
                    ))
            
            # Get switches (if any)
            if hasattr(manager, 'switches') and manager.switches:
                for switch in manager.switches:
                    devices.append(DiscoveredVeSyncDevice(
                        vesync_device_id=switch.cid,
                        device_name=switch.device_name,
                        device_type="switch",
                        model=switch.device_type,
                        is_online=switch.is_online,
                        is_on=switch.is_on,
                        power_w=getattr(switch, 'power', None)
                    ))
            
            return devices
            
        except OutletAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"VeSync device discovery failed: {e}")
            raise OutletConnectionError(f"Device discovery failed: {str(e)}")
    
    async def get_device_state(self, account: VeSyncAccount, vesync_device_id: str) -> Dict[str, Any]:
        """
        Get the current state of a specific device.
        
        Args:
            account: VeSync account
            vesync_device_id: VeSync device ID
            
        Returns:
            Dict[str, Any]: Device state information
            
        Raises:
            OutletAuthenticationError: If credentials are invalid
            OutletConnectionError: If device not found or state fetch fails
        """
        try:
            manager = await self._get_manager(account)
            
            # Find device in outlets
            if hasattr(manager, 'outlets') and manager.outlets:
                for outlet in manager.outlets:
                    if outlet.cid == vesync_device_id:
                        # Update device state
                        await asyncio.to_thread(outlet.update)
                        return {
                            'is_on': outlet.is_on,
                            'is_online': outlet.is_online,
                            'power_w': getattr(outlet, 'power', None),
                            'voltage_v': getattr(outlet, 'voltage', None),
                            'current_a': getattr(outlet, 'current', None),
                            'energy_kwh': getattr(outlet, 'energy', None),
                            'temperature_c': getattr(outlet, 'temperature', None)
                        }
            
            # Find device in switches
            if hasattr(manager, 'switches') and manager.switches:
                for switch in manager.switches:
                    if switch.cid == vesync_device_id:
                        # Update device state
                        await asyncio.to_thread(switch.update)
                        return {
                            'is_on': switch.is_on,
                            'is_online': switch.is_online,
                            'power_w': getattr(switch, 'power', None),
                            'voltage_v': getattr(switch, 'voltage', None),
                            'current_a': getattr(switch, 'current', None),
                            'energy_kwh': getattr(switch, 'energy', None),
                            'temperature_c': getattr(switch, 'temperature', None)
                        }
            
            raise OutletConnectionError(f"Device {vesync_device_id} not found")
            
        except OutletAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get device state for {vesync_device_id}: {e}")
            raise OutletConnectionError(f"Failed to get device state: {str(e)}")
    
    async def turn_device_on(self, account: VeSyncAccount, vesync_device_id: str) -> bool:
        """
        Turn on a specific device.
        
        Args:
            account: VeSync account
            vesync_device_id: VeSync device ID
            
        Returns:
            bool: True if successful
            
        Raises:
            OutletAuthenticationError: If credentials are invalid
            OutletConnectionError: If device not found or control fails
        """
        try:
            manager = await self._get_manager(account)
            
            # Find and control device in outlets
            if hasattr(manager, 'outlets') and manager.outlets:
                for outlet in manager.outlets:
                    if outlet.cid == vesync_device_id:
                        success = await asyncio.to_thread(outlet.turn_on)
                        if not success:
                            raise OutletConnectionError(f"Failed to turn on device {vesync_device_id}")
                        return True
            
            # Find and control device in switches
            if hasattr(manager, 'switches') and manager.switches:
                for switch in manager.switches:
                    if switch.cid == vesync_device_id:
                        success = await asyncio.to_thread(switch.turn_on)
                        if not success:
                            raise OutletConnectionError(f"Failed to turn on device {vesync_device_id}")
                        return True
            
            raise OutletConnectionError(f"Device {vesync_device_id} not found")
            
        except OutletAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to turn on device {vesync_device_id}: {e}")
            raise OutletConnectionError(f"Failed to turn on device: {str(e)}")
    
    async def turn_device_off(self, account: VeSyncAccount, vesync_device_id: str) -> bool:
        """
        Turn off a specific device.
        
        Args:
            account: VeSync account
            vesync_device_id: VeSync device ID
            
        Returns:
            bool: True if successful
            
        Raises:
            OutletAuthenticationError: If credentials are invalid
            OutletConnectionError: If device not found or control fails
        """
        try:
            manager = await self._get_manager(account)
            
            # Find and control device in outlets
            if hasattr(manager, 'outlets') and manager.outlets:
                for outlet in manager.outlets:
                    if outlet.cid == vesync_device_id:
                        success = await asyncio.to_thread(outlet.turn_off)
                        if not success:
                            raise OutletConnectionError(f"Failed to turn off device {vesync_device_id}")
                        return True
            
            # Find and control device in switches
            if hasattr(manager, 'switches') and manager.switches:
                for switch in manager.switches:
                    if switch.cid == vesync_device_id:
                        success = await asyncio.to_thread(switch.turn_off)
                        if not success:
                            raise OutletConnectionError(f"Failed to turn off device {vesync_device_id}")
                        return True
            
            raise OutletConnectionError(f"Device {vesync_device_id} not found")
            
        except OutletAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to turn off device {vesync_device_id}: {e}")
            raise OutletConnectionError(f"Failed to turn off device: {str(e)}")


# Global service instance
vesync_device_service = VeSyncDeviceService() 