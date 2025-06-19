from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timezone, timedelta
from app.db.models import Alert, Device, AlertEvent
from app.schemas.alert import AlertCreate, AlertUpdate, AlertEventCreate, AlertEventUpdate

class AlertCRUD:
    def get(self, db: Session, alert_id: int) -> Optional[Alert]:
        return db.query(Alert).filter(Alert.id == alert_id).first()
    
    def get_by_device(self, db: Session, device_id: int) -> List[Alert]:
        """Get all alerts for a specific device"""
        return db.query(Alert).filter(Alert.device_id == device_id).all()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        device_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        trend_enabled: Optional[bool] = None,
        metric: Optional[str] = None
    ) -> List[Alert]:
        query = db.query(Alert)
        
        if device_id is not None:
            query = query.filter(Alert.device_id == device_id)
        if is_enabled is not None:
            query = query.filter(Alert.is_enabled == is_enabled)
        if trend_enabled is not None:
            query = query.filter(Alert.trend_enabled == trend_enabled)
        if metric is not None:
            query = query.filter(Alert.metric == metric)
        
        return query.offset(skip).limit(limit).all()
    
    def get_with_device_info(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        device_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        trend_enabled: Optional[bool] = None,
        metric: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alerts with device metadata included"""
        query = db.query(Alert, Device).join(Device, Alert.device_id == Device.id)
        
        if device_id is not None:
            query = query.filter(Alert.device_id == device_id)
        if is_enabled is not None:
            query = query.filter(Alert.is_enabled == is_enabled)
        if trend_enabled is not None:
            query = query.filter(Alert.trend_enabled == trend_enabled)
        if metric is not None:
            query = query.filter(Alert.metric == metric)
        
        results = query.offset(skip).limit(limit).all()
        
        # Convert to dictionary format with device info
        alerts_with_device = []
        for alert, device in results:
            alert_dict = {
                "id": alert.id,
                "device_id": alert.device_id,
                "metric": alert.metric,
                "operator": alert.operator,
                "threshold_value": alert.threshold_value,
                "is_enabled": alert.is_enabled,
                "trend_enabled": alert.trend_enabled,
                "created_at": alert.created_at,
                "updated_at": alert.updated_at,
                "device": {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "unit": device.unit,
                    "poll_enabled": device.poll_enabled,
                    "is_active": device.is_active
                }
            }
            alerts_with_device.append(alert_dict)
        
        return alerts_with_device
    
    def get_enabled_alerts(self, db: Session) -> List[Alert]:
        """Get all enabled alerts"""
        return db.query(Alert).filter(Alert.is_enabled == True).all()
    
    def get_trend_alerts(self, db: Session) -> List[Alert]:
        """Get all trend-enabled alerts"""
        return db.query(Alert).filter(Alert.trend_enabled == True).all()
    
    def get_alerts_by_metric(self, db: Session, metric: str) -> List[Alert]:
        """Get all alerts for a specific metric"""
        return db.query(Alert).filter(Alert.metric == metric).all()
    
    def create(self, db: Session, obj_in: AlertCreate) -> Alert:
        db_obj = Alert(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: Alert, 
        obj_in: AlertUpdate
    ) -> Alert:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, alert_id: int) -> Optional[Alert]:
        obj = db.query(Alert).get(alert_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = db.query(Alert).count()
        enabled_alerts = db.query(Alert).filter(Alert.is_enabled == True).count()
        trend_alerts = db.query(Alert).filter(Alert.trend_enabled == True).count()
        
        # Get alert count by device
        alerts_by_device = {}
        results = db.query(Alert, Device).join(Device, Alert.device_id == Device.id).all()
        for alert, device in results:
            device_name = device.name
            if device_name not in alerts_by_device:
                alerts_by_device[device_name] = 0
            alerts_by_device[device_name] += 1
        
        return {
            "total_alerts": total_alerts,
            "enabled_alerts": enabled_alerts,
            "trend_alerts": trend_alerts,
            "alerts_by_device": alerts_by_device
        }

class AlertEventCRUD:
    def get(self, db: Session, event_id: int) -> Optional[AlertEvent]:
        return db.query(AlertEvent).filter(AlertEvent.id == event_id).first()
    
    def get_by_alert(self, db: Session, alert_id: int) -> List[AlertEvent]:
        """Get all events for a specific alert"""
        return db.query(AlertEvent).filter(AlertEvent.alert_id == alert_id).all()
    
    def get_by_device(self, db: Session, device_id: int) -> List[AlertEvent]:
        """Get all events for a specific device"""
        return db.query(AlertEvent).filter(AlertEvent.device_id == device_id).all()
    
    def get_unresolved_events(self, db: Session) -> List[AlertEvent]:
        """Get all unresolved alert events"""
        return db.query(AlertEvent).filter(AlertEvent.is_resolved == False).all()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        alert_id: Optional[int] = None,
        device_id: Optional[int] = None,
        is_resolved: Optional[bool] = None
    ) -> List[AlertEvent]:
        query = db.query(AlertEvent)
        
        if alert_id is not None:
            query = query.filter(AlertEvent.alert_id == alert_id)
        if device_id is not None:
            query = query.filter(AlertEvent.device_id == device_id)
        if is_resolved is not None:
            query = query.filter(AlertEvent.is_resolved == is_resolved)
        
        return query.order_by(desc(AlertEvent.triggered_at)).offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: AlertEventCreate) -> AlertEvent:
        db_obj = AlertEvent(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: AlertEvent, 
        obj_in: AlertEventUpdate
    ) -> AlertEvent:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # Set resolved_at timestamp when marking as resolved
        if update_data.get('is_resolved') and not db_obj.resolved_at:
            db_obj.resolved_at = datetime.now(timezone.utc)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, event_id: int) -> Optional[AlertEvent]:
        obj = db.query(AlertEvent).get(event_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def cleanup_old_events(self, db: Session, days: int = 90) -> int:
        """Delete alert events older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = db.query(AlertEvent).filter(
            AlertEvent.triggered_at < cutoff_date
        ).delete()
        db.commit()
        return result

# Create instances
alert = AlertCRUD()
alert_event = AlertEventCRUD() 