import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_session
from app.crud.device import device as device_crud, history as history_crud
from app.hardware.device_factory import DeviceFactory
from app.hardware.device_base import BaseDevice, PollResult

logger = logging.getLogger(__name__)

class DevicePoller:
    """
    Central device polling service.
    Manages polling of all enabled devices at their specified intervals.
    All timestamps are stored and handled in UTC.
    """
    
    def __init__(self):
        self.running = False
        self.devices: Dict[int, BaseDevice] = {}
        self.poll_tasks: Dict[int, asyncio.Task] = {}
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the polling service"""
        if self.running:
            self.logger.warning("Poller is already running")
            return
        
        self.running = True
        self.logger.info("Starting device poller service")
        
        # Load initial devices
        await self.load_devices()
        
        # Start polling tasks for each device
        await self.start_polling_tasks()
        
        # Start the main polling loop
        asyncio.create_task(self._polling_loop())
    
    async def stop(self):
        """Stop the polling service"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Stopping device poller service")
        
        # Cancel all polling tasks
        for task in self.poll_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.poll_tasks:
            await asyncio.gather(*self.poll_tasks.values(), return_exceptions=True)
        
        self.poll_tasks.clear()
        self.devices.clear()
    
    async def load_devices(self):
        """Load all pollable devices from the database"""
        try:
            async with async_session() as db:
                devices = await device_crud.get_pollable_devices(db)
                
                for db_device in devices:
                    await self.add_device(db_device)
                
                self.logger.info(f"Loaded {len(devices)} devices for polling")
                
        except Exception as e:
            self.logger.error(f"Failed to load devices: {e}")
    
    async def add_device(self, db_device):
        """Add a device to the poller"""
        try:
            device = DeviceFactory.create_device(
                device_type=db_device.device_type,
                device_id=db_device.id,
                name=db_device.name,
                address=db_device.address,
                config=db_device.config
            )
            
            if device:
                self.devices[db_device.id] = device
                self.logger.info(f"Added device to poller: {db_device.name} (unit: {db_device.unit or 'N/A'})")
                
                # Start polling task if poller is running
                if self.running:
                    await self.start_device_polling(db_device.id)
            else:
                self.logger.error(f"Failed to create device: {db_device.name}")
                
        except Exception as e:
            self.logger.error(f"Failed to add device {db_device.name}: {e}")
    
    async def remove_device(self, device_id: int):
        """Remove a device from the poller"""
        if device_id in self.poll_tasks:
            self.poll_tasks[device_id].cancel()
            del self.poll_tasks[device_id]
        
        if device_id in self.devices:
            del self.devices[device_id]
            self.logger.info(f"Removed device from poller: {device_id}")
    
    async def start_polling_tasks(self):
        """Start polling tasks for all devices"""
        for device_id in self.devices:
            await self.start_device_polling(device_id)
    
    async def start_device_polling(self, device_id: int):
        """Start polling task for a specific device"""
        if device_id in self.poll_tasks:
            self.poll_tasks[device_id].cancel()
        
        device = self.devices[device_id]
        task = asyncio.create_task(self._poll_device_loop(device_id))
        self.poll_tasks[device_id] = task
        
        self.logger.info(f"Started polling task for device: {device.name}")
    
    async def _poll_device_loop(self, device_id: int):
        """Poll a specific device at its interval"""
        device = self.devices[device_id]
        
        while self.running:
            try:
                # Get current device config from database
                async with async_session() as db:
                    db_device = await device_crud.get(db, device_id)
                    
                    if not db_device or not db_device.poll_enabled or not db_device.is_active:
                        self.logger.info(f"Device {device.name} is no longer pollable, stopping")
                        break
                    
                    # Poll the device
                    await self._poll_single_device(device_id, db_device)
                    
                    # Wait for next poll interval
                    await asyncio.sleep(db_device.poll_interval)
                
            except asyncio.CancelledError:
                self.logger.info(f"Polling task cancelled for device: {device.name}")
                break
            except Exception as e:
                self.logger.error(f"Error in polling loop for device {device.name}: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _poll_single_device(self, device_id: int, db_device):
        """Poll a single device and store the result"""
        device = self.devices[device_id]
        
        try:
            # Poll the device
            result = await device.safe_poll()
            
            # Store result in database
            await self._store_poll_result(device_id, result)
            
            # Update device status
            await self._update_device_status(device_id, result)
            
        except Exception as e:
            error_msg = f"Failed to poll device {device.name}: {e}"
            self.logger.error(error_msg)
            
            # Update device with error
            await self._update_device_status(device_id, None, error_msg)
    
    async def _store_poll_result(self, device_id: int, result: PollResult):
        """Store poll result in history table"""
        try:
            async with async_session() as db:
                from app.schemas.device import HistoryCreate
                
                history_data = HistoryCreate(
                    device_id=device_id,
                    value=result.value,
                    json_value=result.json_value,
                    history_metadata=result.metadata
                )
                
                await history_crud.create(db, history_data)
                
        except Exception as e:
            self.logger.error(f"Failed to store poll result for device {device_id}: {e}")
    
    async def _update_device_status(self, device_id: int, result: Optional[PollResult], error: Optional[str] = None):
        """Update device's last_polled and last_error fields"""
        try:
            async with async_session() as db:
                last_error = error
                if result and not result.success:
                    last_error = result.error
                
                await device_crud.update_poll_status(
                    db, 
                    device_id=device_id,
                    last_polled=datetime.now(timezone.utc),
                    last_error=last_error
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update device status for device {device_id}: {e}")
    
    async def _polling_loop(self):
        """Main polling loop for periodic tasks"""
        while self.running:
            try:
                # Refresh device list periodically
                await self._refresh_devices()
                
                # Clean up old history data
                await self._cleanup_old_history()
                
                # Wait before next iteration
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in main polling loop: {e}")
                await asyncio.sleep(60)
    
    async def _refresh_devices(self):
        """Refresh the list of pollable devices"""
        try:
            async with async_session() as db:
                current_devices = set(self.devices.keys())
                pollable_devices = await device_crud.get_pollable_devices(db)
                pollable_device_ids = {device.id for device in pollable_devices}
                
                # Remove devices that are no longer pollable
                for device_id in current_devices - pollable_device_ids:
                    await self.remove_device(device_id)
                
                # Add new pollable devices
                for device in pollable_devices:
                    if device.id not in current_devices:
                        await self.add_device(device)
                        
        except Exception as e:
            self.logger.error(f"Failed to refresh devices: {e}")
    
    async def _cleanup_old_history(self):
        """Clean up old history data"""
        try:
            async with async_session() as db:
                deleted_count = await history_crud.cleanup_old_data(db, days=90)
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old history records")
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old history: {e}")
    
    def get_status(self) -> Dict:
        """Get the current status of the poller"""
        return {
            "running": self.running,
            "device_count": len(self.devices),
            "active_tasks": len(self.poll_tasks),
            "devices": [
                {
                    "id": device_id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "unit": device.unit
                }
                for device_id, device in self.devices.items()
            ]
        }

# Global poller instance
poller = DevicePoller() 