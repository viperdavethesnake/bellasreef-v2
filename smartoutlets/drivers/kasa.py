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
from ..schemas import SmartOutletState
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
        """
        super().__init__(device_id, ip_address, auth_info)
        self._logger = logging.getLogger(f"KasaDriver.{device_id}")

    @classmethod
    async def discover_devices(cls) -> List[Dict[str, Any]]:
        """
        Discover Kasa devices on the local network.
        """
        logger = logging.getLogger("KasaDriver.discovery")
        try:
            discovered_devices = await Discover.discover()
            devices = []
            for ip_address, device in discovered_devices.items():
                try:
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
        """Asynchronously creates and updates a SmartPlug instance."""
        plug = SmartPlug(self.ip_address)
        # The update() call is crucial and must be awaited.
        await plug.update()
        return plug

    async def _turn_on_implementation(self) -> bool:
        """
        Implementation of turn on operation.
        """
        async def _turn_on_action():
            try:
                plug = await self._create_smart_plug()
                await plug.turn_on()
                return True
            except (TimeoutError, AuthenticationError, DeviceError, KasaException) as e:
                self._logger.error(f"Error turning on Kasa outlet {self.device_id}: {e}")
                raise OutletConnectionError(f"Failed to turn on outlet: {e}")
        
        return await self._perform_network_action(_turn_on_action)

    async def _turn_off_implementation(self) -> bool:
        """
        Implementation of turn off operation.
        """
        async def _turn_off_action():
            try:
                plug = await self._create_smart_plug()
                await plug.turn_off()
                return True
            except (TimeoutError, AuthenticationError, DeviceError, KasaException) as e:
                self._logger.error(f"Error turning off Kasa outlet {self.device_id}: {e}")
                raise OutletConnectionError(f"Failed to turn off outlet: {e}")

        return await self._perform_network_action(_turn_off_action)

    async def _toggle_implementation(self) -> bool:
        """
        Implementation of toggle operation.
        """
        plug = await self._create_smart_plug()
        if plug.is_on:
            return await self._turn_off_implementation()
        else:
            return await self._turn_on_implementation()

    async def _get_state_implementation(self) -> SmartOutletState:
        """
        Implementation of get state operation.
        """
        plug = await self._create_smart_plug()
        is_on = plug.is_on
        power_w, voltage_v, current_a = None, None, None

        if plug.has_emeter:
            emeter_data = plug.emeter_realtime or {}
            power_w = emeter_data.get('power')
            voltage_v = emeter_data.get('voltage')
            current_ma = emeter_data.get('current')
            current_a = current_ma / 1000.0 if current_ma is not None else None

        return SmartOutletState(
            is_on=is_on,
            power_w=power_w,
            voltage_v=voltage_v,
            current_a=current_a,
            is_online=True
        )

    async def discover_device(self) -> Dict:
        """
        Discover and return Kasa device information.
        """
        plug = await self._create_smart_plug()
        info = plug.sys_info
        return {
            'device_id': self.device_id,
            'ip_address': self.ip_address,
            'alias': info.get('alias', 'Unknown'),
            'model': info.get('model', 'Unknown'),
            'hw_version': info.get('hw_ver', 'Unknown'),
            'sw_version': info.get('sw_ver', 'Unknown'),
            'mac': info.get('mac', 'Unknown'),
            'status': 'connected'
        }

    async def get_energy_meter(self) -> Optional[Dict]:
        """
        Get energy meter data if available.
        """
        plug = await self._create_smart_plug()
        if not plug.has_emeter:
            return None
        
        emeter_data = plug.emeter_realtime or {}
        current_a = emeter_data.get('current', 0) / 1000.0 if emeter_data.get('current') is not None else None
        
        return {
            'power_w': emeter_data.get('power'),
            'voltage_v': emeter_data.get('voltage'),
            'current_a': current_a,
            'total_wh': emeter_data.get('total'),
        } 