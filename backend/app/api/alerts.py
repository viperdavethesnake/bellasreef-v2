from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.crud.alert import alert as alert_crud
from app.crud.device import device as device_crud
from app.schemas.alert import Alert, AlertCreate, AlertUpdate, AlertWithDevice, AlertStats

router = APIRouter()

@router.get("/", response_model=List[Alert])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    is_enabled: Optional[bool] = None,
    trend_enabled: Optional[bool] = None,
    metric: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all alerts with optional filtering"""
    alerts = alert_crud.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        device_id=device_id,
        is_enabled=is_enabled,
        trend_enabled=trend_enabled,
        metric=metric
    )
    return alerts

@router.get("/with-device")
def get_alerts_with_device_info(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    is_enabled: Optional[bool] = None,
    trend_enabled: Optional[bool] = None,
    metric: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get alerts with device metadata included"""
    alerts_with_device = alert_crud.get_with_device_info(
        db, 
        skip=skip, 
        limit=limit,
        device_id=device_id,
        is_enabled=is_enabled,
        trend_enabled=trend_enabled,
        metric=metric
    )
    return alerts_with_device

@router.get("/stats", response_model=AlertStats)
def get_alert_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get alert statistics"""
    stats = alert_crud.get_stats(db)
    return AlertStats(**stats)

@router.get("/metrics", response_model=List[str])
def get_alert_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all unique metrics used in alerts"""
    alerts = alert_crud.get_multi(db, limit=1000)
    metrics = list(set(alert.metric for alert in alerts))
    return sorted(metrics)

@router.get("/{alert_id}", response_model=Alert)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific alert by ID"""
    alert = alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    return alert

@router.get("/{alert_id}/with-device")
def get_alert_with_device_info(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific alert with device metadata included"""
    alert = alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Get device info
    device = device_crud.get(db, device_id=alert.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated device not found"
        )
    
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
    
    return alert_dict

@router.post("/", response_model=Alert)
def create_alert(
    alert_in: AlertCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new alert"""
    # Validate device exists
    device = device_crud.get(db, device_id=alert_in.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Validate device is active
    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create alert for inactive device"
        )
    
    # Validate trend alert requirements
    if alert_in.trend_enabled and not device.poll_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trend alerts can only be created for devices with polling enabled"
        )
    
    alert = alert_crud.create(db, obj_in=alert_in)
    return alert

@router.put("/{alert_id}", response_model=Alert)
def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an alert"""
    alert = alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # If device_id is being changed, validate the new device
    if alert_in.device_id is not None and alert_in.device_id != alert.device_id:
        device = device_crud.get(db, device_id=alert_in.device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        if not device.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move alert to inactive device"
            )
        
        # Check trend alert requirements for new device
        if alert_in.trend_enabled is not None and alert_in.trend_enabled and not device.poll_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trend alerts can only be created for devices with polling enabled"
            )
    
    # If trend_enabled is being enabled, validate current device supports polling
    if alert_in.trend_enabled is not None and alert_in.trend_enabled:
        device = device_crud.get(db, device_id=alert.device_id)
        if not device.poll_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trend alerts can only be enabled for devices with polling enabled"
            )
    
    alert = alert_crud.update(db, db_obj=alert, obj_in=alert_in)
    return alert

@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an alert"""
    alert = alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert_crud.remove(db, alert_id=alert_id)
    return {"message": "Alert deleted successfully"}

@router.get("/device/{device_id}", response_model=List[Alert])
def get_device_alerts(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all alerts for a specific device"""
    # Verify device exists
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    alerts = alert_crud.get_by_device(db, device_id=device_id)
    return alerts

@router.post("/{alert_id}/enable")
def enable_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Enable an alert"""
    alert = alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert = alert_crud.update(db, db_obj=alert, obj_in=AlertUpdate(is_enabled=True))
    return {"message": "Alert enabled successfully", "alert": alert}

@router.post("/{alert_id}/disable")
def disable_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Disable an alert"""
    alert = alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert = alert_crud.update(db, db_obj=alert, obj_in=AlertUpdate(is_enabled=False))
    return {"message": "Alert disabled successfully", "alert": alert} 