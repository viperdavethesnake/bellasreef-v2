from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.api.deps import get_current_user
from shared.crud.alert import alert as alert_crud
from shared.crud.device import device as device_crud
from shared.schemas.alert import Alert, AlertCreate, AlertUpdate, AlertWithDevice, AlertStats
from shared.db.database import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=List[Alert])
async def get_alerts(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    is_enabled: Optional[bool] = None,
    trend_enabled: Optional[bool] = None,
    metric: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all alerts with optional filtering"""
    alerts = await alert_crud.get_multi(
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
async def get_alerts_with_device_info(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    is_enabled: Optional[bool] = None,
    trend_enabled: Optional[bool] = None,
    metric: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get alerts with device metadata included"""
    alerts_with_device = await alert_crud.get_multi_with_device_info(
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
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get alert statistics"""
    stats = await alert_crud.get_stats(db)
    return AlertStats(**stats)

@router.get("/metrics", response_model=List[str])
async def get_alert_metrics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all unique metrics used in alerts"""
    alerts = await alert_crud.get_multi(db, limit=1000)
    metrics = list(set(alert.metric for alert in alerts))
    return sorted(metrics)

@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific alert by ID"""
    alert = await alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    return alert

@router.get("/{alert_id}/with-device")
async def get_alert_with_device_info(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific alert with device metadata included"""
    alert = await alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Get device info
    device = await device_crud.get(db, device_id=alert.device_id)
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
            "unit": device.unit
        }
    }
    
    return alert_dict

@router.post("/", response_model=Alert)
async def create_alert(
    alert_in: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new alert"""
    # Validate device exists
    device = await device_crud.get(db, device_id=alert_in.device_id)
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
    
    alert = await alert_crud.create(db, obj_in=alert_in)
    return alert

@router.put("/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an alert"""
    alert = await alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # If device_id is being changed, validate the new device
    if alert_in.device_id is not None and alert_in.device_id != alert.device_id:
        device = await device_crud.get(db, device_id=alert_in.device_id)
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
    
    alert = await alert_crud.update(db, db_obj=alert, obj_in=alert_in)
    return alert

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an alert"""
    alert = await alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    await alert_crud.remove(db, alert_id=alert_id)
    return {"message": "Alert deleted successfully"}

@router.get("/device/{device_id}", response_model=List[Alert])
async def get_device_alerts(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all alerts for a specific device"""
    # Verify device exists
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    alerts = await alert_crud.get_by_device(db, device_id=device_id)
    return alerts

@router.post("/{alert_id}/enable")
async def enable_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Enable an alert"""
    alert = await alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already enabled"
        )
    
    alert_update = AlertUpdate(is_enabled=True)
    alert = await alert_crud.update(db, db_obj=alert, obj_in=alert_update)
    return {"message": "Alert enabled successfully", "alert": alert}

@router.post("/{alert_id}/disable")
async def disable_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Disable an alert"""
    alert = await alert_crud.get(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if not alert.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already disabled"
        )
    
    alert_update = AlertUpdate(is_enabled=False)
    alert = await alert_crud.update(db, db_obj=alert, obj_in=alert_update)
    return {"message": "Alert disabled successfully", "alert": alert} 