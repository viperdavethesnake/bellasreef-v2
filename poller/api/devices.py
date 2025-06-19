from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.api.deps import get_current_user
from shared.crud.device import device as device_crud, history as history_crud
from shared.schemas.device import Device, DeviceCreate, DeviceUpdate, History, DeviceWithHistory, HistoryWithDevice, DeviceStats
from poller.services.poller import poller
from control.hardware.device_factory import DeviceFactory
from shared.db.database import get_db

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("/", response_model=List[Device])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    poll_enabled: Optional[bool] = None,
    device_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    unit: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all devices with optional filtering"""
    devices = await device_crud.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        poll_enabled=poll_enabled,
        device_type=device_type,
        is_active=is_active,
        unit=unit
    )
    return devices

@router.get("/types", response_model=List[str])
def get_device_types(current_user = Depends(get_current_user)):
    """Get all available device types"""
    return DeviceFactory.get_available_device_types()

@router.get("/units", response_model=List[str])
async def get_device_units(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all unique units used by devices"""
    # Get all devices and extract unique units
    devices = await device_crud.get_multi(db, limit=1000)
    units = list(set(device.unit for device in devices if device.unit))
    return sorted(units)

@router.get("/by-unit/{unit}", response_model=List[Device])
async def get_devices_by_unit(
    unit: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all devices with a specific unit of measurement"""
    devices = await device_crud.get_devices_by_unit(db, unit)
    return devices

@router.get("/{device_id}", response_model=Device)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific device by ID"""
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return device

@router.post("/", response_model=Device)
async def create_device(
    device_in: DeviceCreate,
    db: AsyncSession = Depends(get_db),
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
    existing_device = await device_crud.get_by_address(db, device_in.address)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with address {device_in.address} already exists"
        )
    
    device = await device_crud.create(db, obj_in=device_in)
    return device

@router.put("/{device_id}", response_model=Device)
async def update_device(
    device_id: int,
    device_in: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a device"""
    device = await device_crud.get(db, device_id=device_id)
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
        existing_device = await device_crud.get_by_address(db, device_in.address)
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device with address {device_in.address} already exists"
            )
    
    device = await device_crud.update(db, db_obj=device, obj_in=device_in)
    return device

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a device"""
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    await device_crud.remove(db, device_id=device_id)
    return {"message": "Device deleted successfully"}

@router.get("/{device_id}/history", response_model=List[History])
async def get_device_history(
    device_id: int,
    skip: int = 0,
    limit: int = 100,
    hours: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get history for a specific device"""
    # Verify device exists
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    history = await history_crud.get_by_device(
        db, 
        device_id=device_id, 
        skip=skip, 
        limit=limit,
        hours=hours
    )
    return history

@router.get("/{device_id}/history-with-device")
async def get_device_history_with_device_info(
    device_id: int,
    skip: int = 0,
    limit: int = 100,
    hours: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get history for a specific device with device metadata included"""
    # Verify device exists
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    history_with_device = await history_crud.get_by_device_with_device_info(
        db, 
        device_id=device_id, 
        skip=skip, 
        limit=limit,
        hours=hours
    )
    return history_with_device

@router.get("/{device_id}/latest", response_model=History)
async def get_device_latest(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the latest reading for a specific device"""
    # Verify device exists
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    latest = await history_crud.get_latest_by_device(db, device_id=device_id)
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No history found for this device"
        )
    
    return latest

@router.get("/{device_id}/latest-with-device")
async def get_device_latest_with_device_info(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the latest reading for a specific device with device metadata included"""
    # Verify device exists
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    latest_with_device = await history_crud.get_latest_by_device_with_device_info(db, device_id=device_id)
    if not latest_with_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No history found for this device"
        )
    
    return latest_with_device

@router.get("/{device_id}/stats", response_model=DeviceStats)
async def get_device_stats(
    device_id: int,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get statistics for a specific device over the specified time period"""
    # Verify device exists
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    stats = await history_crud.get_device_stats(db, device_id=device_id, hours=hours)
    return stats

@router.post("/{device_id}/test")
async def test_device_connection(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test the connection to a specific device"""
    # Get the device
    device = await device_crud.get(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    try:
        # Create device instance and test connection
        device_instance = DeviceFactory.create_device(device.device_type, device.address)
        result = await device_instance.test_connection()
        
        return {
            "device_id": device_id,
            "device_name": device.name,
            "device_type": device.device_type,
            "address": device.address,
            "connection_test": result,
            "timestamp": result.get("timestamp") if result else None
        }
    except Exception as e:
        return {
            "device_id": device_id,
            "device_name": device.name,
            "device_type": device.device_type,
            "address": device.address,
            "connection_test": {
                "success": False,
                "error": str(e)
            },
            "timestamp": None
        }

@router.get("/poller/status")
def get_poller_status(current_user = Depends(get_current_user)):
    """Get the current status of the device poller"""
    return poller.get_status()

@router.post("/poller/start")
def start_poller(current_user = Depends(get_current_user)):
    """Start the device poller"""
    poller.start()
    return {"message": "Poller started successfully"}

@router.post("/poller/stop")
def stop_poller(current_user = Depends(get_current_user)):
    """Stop the device poller"""
    poller.stop()
    return {"message": "Poller stopped successfully"} 