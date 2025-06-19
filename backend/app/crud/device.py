from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta, timezone
from app.db.models import Device, History
from app.schemas.device import DeviceCreate, DeviceUpdate, HistoryCreate

class DeviceCRUD:
    def get(self, db: Session, device_id: int) -> Optional[Device]:
        return db.query(Device).filter(Device.id == device_id).first()
    
    def get_by_address(self, db: Session, address: str) -> Optional[Device]:
        return db.query(Device).filter(Device.address == address).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        poll_enabled: Optional[bool] = None,
        device_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        unit: Optional[str] = None
    ) -> List[Device]:
        query = db.query(Device)
        
        if poll_enabled is not None:
            query = query.filter(Device.poll_enabled == poll_enabled)
        if device_type is not None:
            query = query.filter(Device.device_type == device_type)
        if is_active is not None:
            query = query.filter(Device.is_active == is_active)
        if unit is not None:
            query = query.filter(Device.unit == unit)
        
        return query.offset(skip).limit(limit).all()
    
    def get_pollable_devices(self, db: Session) -> List[Device]:
        """Get all devices that should be polled (enabled and active)"""
        return db.query(Device).filter(
            and_(
                Device.poll_enabled == True,
                Device.is_active == True
            )
        ).all()
    
    def get_devices_by_unit(self, db: Session, unit: str) -> List[Device]:
        """Get all devices with a specific unit of measurement"""
        return db.query(Device).filter(Device.unit == unit).all()
    
    def create(self, db: Session, obj_in: DeviceCreate) -> Device:
        db_obj = Device(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: Device, 
        obj_in: DeviceUpdate
    ) -> Device:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_poll_status(
        self, 
        db: Session, 
        device_id: int, 
        last_polled: datetime,
        last_error: Optional[str] = None
    ) -> Optional[Device]:
        device = self.get(db, device_id)
        if device:
            device.last_polled = last_polled
            device.last_error = last_error
            device.updated_at = datetime.now(timezone.utc)
            db.add(device)
            db.commit()
            db.refresh(device)
        return device
    
    def remove(self, db: Session, device_id: int) -> Optional[Device]:
        obj = db.query(Device).get(device_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

class HistoryCRUD:
    def get(self, db: Session, history_id: int) -> Optional[History]:
        return db.query(History).filter(History.id == history_id).first()
    
    def get_by_device(
        self, 
        db: Session, 
        device_id: int, 
        skip: int = 0, 
        limit: int = 100,
        hours: Optional[int] = None
    ) -> List[History]:
        query = db.query(History).filter(History.device_id == device_id)
        
        if hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(History.timestamp >= cutoff_time)
        
        return query.order_by(desc(History.timestamp)).offset(skip).limit(limit).all()
    
    def get_by_device_with_device_info(
        self, 
        db: Session, 
        device_id: int, 
        skip: int = 0, 
        limit: int = 100,
        hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get history records with device metadata included"""
        query = db.query(History, Device).join(Device, History.device_id == Device.id).filter(History.device_id == device_id)
        
        if hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(History.timestamp >= cutoff_time)
        
        results = query.order_by(desc(History.timestamp)).offset(skip).limit(limit).all()
        
        # Convert to dictionary format with device info
        history_with_device = []
        for history, device in results:
            history_dict = {
                "id": history.id,
                "device_id": history.device_id,
                "timestamp": history.timestamp,
                "value": history.value,
                "json_value": history.json_value,
                "metadata": history.metadata,
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
    
    def get_latest_by_device(self, db: Session, device_id: int) -> Optional[History]:
        return db.query(History).filter(
            History.device_id == device_id
        ).order_by(desc(History.timestamp)).first()
    
    def get_latest_by_device_with_device_info(self, db: Session, device_id: int) -> Optional[Dict[str, Any]]:
        """Get latest history record with device metadata included"""
        result = db.query(History, Device).join(Device, History.device_id == Device.id).filter(
            History.device_id == device_id
        ).order_by(desc(History.timestamp)).first()
        
        if result:
            history, device = result
            return {
                "id": history.id,
                "device_id": history.device_id,
                "timestamp": history.timestamp,
                "value": history.value,
                "json_value": history.json_value,
                "metadata": history.metadata,
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
    
    def create(self, db: Session, obj_in: HistoryCreate) -> History:
        db_obj = History(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def cleanup_old_data(self, db: Session, days: int = 90) -> int:
        """Delete history data older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = db.query(History).filter(
            History.timestamp < cutoff_date
        ).delete()
        db.commit()
        return result
    
    def get_device_stats(
        self, 
        db: Session, 
        device_id: int, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get basic statistics for a device over the specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get device info for unit
        device = device_crud.get(db, device_id)
        unit = device.unit if device else None
        
        # Get all numeric values in the time period
        values = db.query(History.value).filter(
            and_(
                History.device_id == device_id,
                History.timestamp >= cutoff_time,
                History.value.isnot(None)
            )
        ).all()
        
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
        numeric_values = [v[0] for v in values if v[0] is not None]
        
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