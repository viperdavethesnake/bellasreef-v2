from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.crud.device import device as device_crud, history as history_crud
from app.schemas.device import Device, DeviceCreate, DeviceUpdate, History, DeviceWithHistory
from app.services.poller import poller
from app.hardware.device_factory import DeviceFactory

router = APIRouter()

@router.get("/", response_model=List[Device])
def get_devices(
    skip: int = 0,
    limit: int = 100,
    poll_enabled: Optional[bool] = None,
    device_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all devices with optional filtering"""
    devices = device_crud.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        poll_enabled=poll_enabled,
        device_type=device_type,
        is_active=is_active
    )
    return devices

@router.get("/types", response_model=List[str])
def get_device_types(current_user = Depends(get_current_user)):
    """Get all available device types"""
    return DeviceFactory.get_available_device_types()

@router.get("/{device_id}", response_model=Device)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific device by ID"""
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return device

@router.post("/", response_model=Device)
def create_device(
    device_in: DeviceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new device"""
    # Validate device type
    if device_in.device_type not in DeviceFactory.get_available_device_types():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown device type: {device_in.device_type}"
        )
    
    # Check if device with same address already exists
    existing_device = device_crud.get_by_address(db, device_in.address)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with address {device_in.address} already exists"
        )
    
    device = device_crud.create(db, obj_in=device_in)
    return device

@router.put("/{device_id}", response_model=Device)
def update_device(
    device_id: int,
    device_in: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a device"""
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Validate device type if being changed
    if device_in.device_type and device_in.device_type not in DeviceFactory.get_available_device_types():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown device type: {device_in.device_type}"
        )
    
    # Check address uniqueness if being changed
    if device_in.address and device_in.address != device.address:
        existing_device = device_crud.get_by_address(db, device_in.address)
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device with address {device_in.address} already exists"
            )
    
    device = device_crud.update(db, db_obj=device, obj_in=device_in)
    return device

@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a device"""
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_crud.remove(db, device_id=device_id)
    return {"message": "Device deleted successfully"}

@router.get("/{device_id}/history", response_model=List[History])
def get_device_history(
    device_id: int,
    skip: int = 0,
    limit: int = 100,
    hours: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get history for a specific device"""
    # Verify device exists
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    history = history_crud.get_by_device(
        db, 
        device_id=device_id, 
        skip=skip, 
        limit=limit,
        hours=hours
    )
    return history

@router.get("/{device_id}/latest", response_model=History)
def get_device_latest(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the latest reading for a device"""
    # Verify device exists
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    latest = history_crud.get_latest_by_device(db, device_id=device_id)
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No history data found for this device"
        )
    
    return latest

@router.get("/{device_id}/stats")
def get_device_stats(
    device_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get statistics for a device over a time period"""
    # Verify device exists
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    stats = history_crud.get_device_stats(db, device_id=device_id, hours=hours)
    return {
        "device_id": device_id,
        "device_name": device.name,
        "hours": hours,
        "stats": stats
    }

@router.post("/{device_id}/test")
def test_device_connection(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test connection to a device"""
    device = device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Create device instance for testing
    device_instance = DeviceFactory.create_device(
        device_type=device.device_type,
        device_id=device.id,
        name=device.name,
        address=device.address,
        config=device.config
    )
    
    if not device_instance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create device instance for type: {device.device_type}"
        )
    
    # Test connection (this would need to be async in a real implementation)
    # For now, return a placeholder response
    return {
        "device_id": device_id,
        "device_name": device.name,
        "test_result": "Test endpoint - implement actual device testing",
        "status": "pending"
    }

@router.get("/poller/status")
def get_poller_status(current_user = Depends(get_current_user)):
    """Get the current status of the device poller"""
    return poller.get_status()

@router.post("/poller/start")
def start_poller(current_user = Depends(get_current_user)):
    """Start the device poller"""
    # This would need to be async in a real implementation
    return {
        "message": "Poller start endpoint - implement actual poller start",
        "status": "pending"
    }

@router.post("/poller/stop")
def stop_poller(current_user = Depends(get_current_user)):
    """Stop the device poller"""
    # This would need to be async in a real implementation
    return {
        "message": "Poller stop endpoint - implement actual poller stop",
        "status": "pending"
    } 