from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta, timezone
from shared.db.models import Device, History
from shared.schemas.device import DeviceCreate, DeviceUpdate, HistoryCreate

class DeviceCRUD:
    async def get(self, db: AsyncSession, device_id: int) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.id == device_id))
        return result.scalar_one_or_none()
    
    async def get_by_address(self, db: AsyncSession, address: str) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.address == address).unique())
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        poll_enabled: Optional[bool] = None,
        device_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        unit: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[Device]:
        query = select(Device)
        
        if poll_enabled is not None:
            query = query.filter(Device.poll_enabled == poll_enabled)
        if device_type is not None:
            query = query.filter(Device.device_type == device_type)
        if is_active is not None:
            query = query.filter(Device.is_active == is_active)
        if unit is not None:
            query = query.filter(Device.unit == unit)
        if role is not None:
            query = query.filter(Device.role == role)
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_pollable_devices(self, db: AsyncSession) -> List[Device]:
        """Get all devices that should be polled (enabled and active)"""
        result = await db.execute(
            select(Device).filter(
                and_(
                    Device.poll_enabled == True,
                    Device.is_active == True
                )
            )
        )
        return result.scalars().all()
    
    async def get_devices_by_unit(self, db: AsyncSession, unit: str) -> List[Device]:
        """Get all devices with a specific unit of measurement"""
        result = await db.execute(select(Device).filter(Device.unit == unit))
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, obj_in: DeviceCreate) -> Device:
        db_obj = Device(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
        db_obj: Device, 
        obj_in: DeviceUpdate
    ) -> Device:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_poll_status(
        self,
        db: AsyncSession,
        device_id: int,
        last_error: Optional[str] = None
    ) -> Optional[Device]:
        """Updates a device's last_polled timestamp and optional error message."""
        device = await self.get(db, device_id=device_id)
        if device:
            device.last_polled = datetime.now(timezone.utc)
            device.last_error = last_error
            db.add(device)
            await db.commit()
            await db.refresh(device)
        return device
    
    async def remove(self, db: AsyncSession, device_id: int) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.id == device_id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

class HistoryCRUD:
    async def get(self, db: AsyncSession, history_id: int) -> Optional[History]:
        result = await db.execute(select(History).filter(History.id == history_id))
        return result.scalar_one_or_none()
    
    async def get_by_device(
        self, 
        db: AsyncSession, 
        device_id: int, 
        skip: int = 0, 
        limit: int = 100,
        hours: Optional[int] = None
    ) -> List[History]:
        query = select(History).filter(History.device_id == device_id)
        
        if hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(History.timestamp >= cutoff_time)
        
        result = await db.execute(query.order_by(desc(History.timestamp)).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_by_device_with_device_info(
        self, 
        db: AsyncSession, 
        device_id: int, 
        skip: int = 0, 
        limit: int = 100,
        hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get history records with device metadata included"""
        query = select(History, Device).join(Device, History.device_id == Device.id).filter(History.device_id == device_id)
        
        if hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(History.timestamp >= cutoff_time)
        
        result = await db.execute(query.order_by(desc(History.timestamp)).offset(skip).limit(limit))
        results = result.all()
        
        # Convert to dictionary format with device info
        history_with_device = []
        for history, device in results:
            history_dict = {
                "id": history.id,
                "device_id": history.device_id,
                "timestamp": history.timestamp,
                "value": history.value,
                "json_value": history.json_value,
                "history_metadata": history.history_metadata,
                "device": {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "unit": device.unit,
                    "min_value": device.min_value,
                    "max_value": device.max_value
                }
            }
            history_with_device.append(history_dict)
        
        return history_with_device
    
    async def get_latest_by_device(self, db: AsyncSession, device_id: int) -> Optional[History]:
        result = await db.execute(
            select(History).filter(
                History.device_id == device_id
            ).order_by(desc(History.timestamp))
        )
        return result.scalar_one_or_none()
    
    async def get_latest_by_device_with_device_info(self, db: AsyncSession, device_id: int) -> Optional[Dict[str, Any]]:
        """Get latest history record with device metadata included"""
        result = await db.execute(
            select(History, Device).join(Device, History.device_id == Device.id).filter(
                History.device_id == device_id
            ).order_by(desc(History.timestamp))
        )
        row = result.first()
        
        if row:
            history, device = row
            return {
                "id": history.id,
                "device_id": history.device_id,
                "timestamp": history.timestamp,
                "value": history.value,
                "json_value": history.json_value,
                "history_metadata": history.history_metadata,
                "device": {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "unit": device.unit,
                    "min_value": device.min_value,
                    "max_value": device.max_value
                }
            }
        return None
    
    async def create(self, db: AsyncSession, obj_in: HistoryCreate) -> History:
        db_obj = History(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def cleanup_old_data(self, db: AsyncSession, days: int = 90) -> int:
        """Delete history data older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(History).filter(
                History.timestamp < cutoff_date
            )
        )
        old_records = result.scalars().all()
        
        for record in old_records:
            await db.delete(record)
        
        await db.commit()
        return len(old_records)
    
    async def get_device_stats(
        self, 
        db: AsyncSession, 
        device_id: int, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get basic statistics for a device over the specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get device info for unit
        device = await device_crud.get(db, device_id)
        unit = device.unit if device else None
        
        # Get all numeric values in the time period
        result = await db.execute(
            select(History.value).filter(
                and_(
                    History.device_id == device_id,
                    History.timestamp >= cutoff_time,
                    History.value.isnot(None)
                )
            )
        )
        values = result.scalars().all()
        
        if not values:
            return {
                "device_id": device_id,
                "device_name": device.name if device else "Unknown",
                "unit": unit,
                "hours": hours,
                "stats": {
                    "count": 0,
                    "min": None,
                    "max": None,
                    "avg": None,
                    "latest": None
                }
            }
        
        # Extract numeric values
        numeric_values = [v for v in values if v is not None]
        
        if not numeric_values:
            return {
                "device_id": device_id,
                "device_name": device.name if device else "Unknown",
                "unit": unit,
                "hours": hours,
                "stats": {
                    "count": 0,
                    "min": None,
                    "max": None,
                    "avg": None,
                    "latest": None
                }
            }
        
        return {
            "device_id": device_id,
            "device_name": device.name if device else "Unknown",
            "unit": unit,
            "hours": hours,
            "stats": {
                "count": len(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values),
                "latest": numeric_values[0] if numeric_values else None
            }
        }

device = DeviceCRUD()
history = HistoryCRUD() 