from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timezone, timedelta
from shared.db.models import Alert, Device, AlertEvent
from shared.schemas.alert import AlertCreate, AlertUpdate, AlertEventCreate, AlertEventUpdate

class AlertCRUD:
    async def get(self, db: AsyncSession, alert_id: int) -> Optional[Alert]:
        result = await db.execute(select(Alert).filter(Alert.id == alert_id))
        return result.scalar_one_or_none()
    
    async def get_by_device(self, db: AsyncSession, device_id: int) -> List[Alert]:
        """Get all alerts for a specific device"""
        result = await db.execute(select(Alert).filter(Alert.device_id == device_id))
        return result.scalars().all()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        device_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        trend_enabled: Optional[bool] = None,
        metric: Optional[str] = None
    ) -> List[Alert]:
        query = select(Alert)
        
        if device_id is not None:
            query = query.filter(Alert.device_id == device_id)
        if is_enabled is not None:
            query = query.filter(Alert.is_enabled == is_enabled)
        if trend_enabled is not None:
            query = query.filter(Alert.trend_enabled == trend_enabled)
        if metric is not None:
            query = query.filter(Alert.metric == metric)
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_multi_with_device_info(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        device_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        trend_enabled: Optional[bool] = None,
        metric: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alerts with device metadata included"""
        query = select(Alert, Device).join(Device, Alert.device_id == Device.id)
        
        if device_id is not None:
            query = query.filter(Alert.device_id == device_id)
        if is_enabled is not None:
            query = query.filter(Alert.is_enabled == is_enabled)
        if trend_enabled is not None:
            query = query.filter(Alert.trend_enabled == trend_enabled)
        if metric is not None:
            query = query.filter(Alert.metric == metric)
        
        result = await db.execute(query.offset(skip).limit(limit))
        results = result.all()
        
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
                    "unit": device.unit
                }
            }
            alerts_with_device.append(alert_dict)
        
        return alerts_with_device
    
    async def get_enabled_alerts(self, db: AsyncSession) -> List[Alert]:
        """Get all enabled alerts"""
        result = await db.execute(select(Alert).filter(Alert.is_enabled == True))
        return result.scalars().all()
    
    async def get_trend_alerts(self, db: AsyncSession) -> List[Alert]:
        """Get all trend-enabled alerts"""
        result = await db.execute(select(Alert).filter(Alert.trend_enabled == True))
        return result.scalars().all()
    
    async def get_by_metric(self, db: AsyncSession, metric: str) -> List[Alert]:
        """Get all alerts for a specific metric"""
        result = await db.execute(select(Alert).filter(Alert.metric == metric))
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, obj_in: AlertCreate) -> Alert:
        db_obj = Alert(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
        db_obj: Alert, 
        obj_in: AlertUpdate
    ) -> Alert:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove(self, db: AsyncSession, alert_id: int) -> Optional[Alert]:
        result = await db.execute(select(Alert).filter(Alert.id == alert_id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get alert statistics"""
        # Total alerts
        result = await db.execute(select(func.count(Alert.id)))
        total_alerts = result.scalar()
        
        # Enabled alerts
        result = await db.execute(select(func.count(Alert.id)).filter(Alert.is_enabled == True))
        enabled_alerts = result.scalar()
        
        # Trend alerts
        result = await db.execute(select(func.count(Alert.id)).filter(Alert.trend_enabled == True))
        trend_alerts = result.scalar()
        
        # Alerts with device info
        result = await db.execute(
            select(Alert, Device).join(Device, Alert.device_id == Device.id)
        )
        results = result.all()
        
        # Group by device type
        device_type_counts = {}
        for alert, device in results:
            device_type = device.device_type
            if device_type not in device_type_counts:
                device_type_counts[device_type] = 0
            device_type_counts[device_type] += 1
        
        return {
            "total_alerts": total_alerts,
            "enabled_alerts": enabled_alerts,
            "trend_alerts": trend_alerts,
            "device_type_counts": device_type_counts
        }

class AlertEventCRUD:
    async def get(self, db: AsyncSession, event_id: int) -> Optional[AlertEvent]:
        result = await db.execute(select(AlertEvent).filter(AlertEvent.id == event_id))
        return result.scalar_one_or_none()
    
    async def get_by_alert(self, db: AsyncSession, alert_id: int) -> List[AlertEvent]:
        """Get all events for a specific alert"""
        result = await db.execute(select(AlertEvent).filter(AlertEvent.alert_id == alert_id))
        return result.scalars().all()
    
    async def get_by_device(self, db: AsyncSession, device_id: int) -> List[AlertEvent]:
        """Get all events for a specific device"""
        result = await db.execute(select(AlertEvent).filter(AlertEvent.device_id == device_id))
        return result.scalars().all()
    
    async def get_unresolved(self, db: AsyncSession) -> List[AlertEvent]:
        """Get all unresolved alert events"""
        result = await db.execute(select(AlertEvent).filter(AlertEvent.is_resolved == False))
        return result.scalars().all()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        alert_id: Optional[int] = None,
        device_id: Optional[int] = None,
        is_resolved: Optional[bool] = None
    ) -> List[AlertEvent]:
        query = select(AlertEvent)
        
        if alert_id is not None:
            query = query.filter(AlertEvent.alert_id == alert_id)
        if device_id is not None:
            query = query.filter(AlertEvent.device_id == device_id)
        if is_resolved is not None:
            query = query.filter(AlertEvent.is_resolved == is_resolved)
        
        result = await db.execute(query.order_by(desc(AlertEvent.triggered_at)).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, obj_in: AlertEventCreate) -> AlertEvent:
        db_obj = AlertEvent(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
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
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove(self, db: AsyncSession, event_id: int) -> Optional[AlertEvent]:
        result = await db.execute(select(AlertEvent).filter(AlertEvent.id == event_id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def cleanup_old_events(self, db: AsyncSession, days: int = 30) -> int:
        """Delete alert events older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(AlertEvent).filter(
                AlertEvent.triggered_at < cutoff_date
            )
        )
        old_events = result.scalars().all()
        
        for event in old_events:
            await db.delete(event)
        
        await db.commit()
        return len(old_events)

# Create instances
alert = AlertCRUD()
alert_event = AlertEventCRUD() 