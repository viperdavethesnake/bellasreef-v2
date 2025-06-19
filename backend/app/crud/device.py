from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
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
        is_active: Optional[bool] = None
    ) -> List[Device]:
        query = db.query(Device)
        
        if poll_enabled is not None:
            query = query.filter(Device.poll_enabled == poll_enabled)
        if device_type is not None:
            query = query.filter(Device.device_type == device_type)
        if is_active is not None:
            query = query.filter(Device.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_pollable_devices(self, db: Session) -> List[Device]:
        """Get all devices that should be polled (enabled and active)"""
        return db.query(Device).filter(
            and_(
                Device.poll_enabled == True,
                Device.is_active == True
            )
        ).all()
    
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
        
        db_obj.updated_at = datetime.utcnow()
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
            device.updated_at = datetime.utcnow()
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
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(History.timestamp >= cutoff_time)
        
        return query.order_by(desc(History.timestamp)).offset(skip).limit(limit).all()
    
    def get_latest_by_device(self, db: Session, device_id: int) -> Optional[History]:
        return db.query(History).filter(
            History.device_id == device_id
        ).order_by(desc(History.timestamp)).first()
    
    def create(self, db: Session, obj_in: HistoryCreate) -> History:
        db_obj = History(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def cleanup_old_data(self, db: Session, days: int = 90) -> int:
        """Delete history data older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
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
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
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
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "latest": None
            }
        
        # Extract numeric values
        numeric_values = [v[0] for v in values if v[0] is not None]
        
        if not numeric_values:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "latest": None
            }
        
        return {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
            "latest": numeric_values[0] if numeric_values else None
        }

device = DeviceCRUD()
history = HistoryCRUD() 