from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.crud.schedule import schedule as schedule_crud, device_action as device_action_crud
from app.schemas.schedule import (
    Schedule, ScheduleCreate, ScheduleUpdate, ScheduleStats,
    DeviceAction, DeviceActionCreate, DeviceActionUpdate, DeviceActionStats,
    DeviceActionWithDevice, SchedulerHealth
)
from app.db.models import User, Device
from datetime import datetime, timezone

router = APIRouter()

# Schedule endpoints
@router.get("/", response_model=List[Schedule])
def get_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    schedule_type: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all schedules with optional filtering.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **schedule_type**: Filter by schedule type (one_off, recurring, interval, cron, static)
    - **is_enabled**: Filter by enabled status
    - **device_id**: Filter schedules that target a specific device
    """
    schedules = schedule_crud.get_multi(
        db, skip=skip, limit=limit,
        schedule_type=schedule_type,
        is_enabled=is_enabled,
        device_id=device_id
    )
    return schedules

@router.get("/stats", response_model=ScheduleStats)
def get_schedule_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get schedule statistics and next run times."""
    return schedule_crud.get_stats(db)

@router.get("/{schedule_id}", response_model=Schedule)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific schedule by ID."""
    schedule = schedule_crud.get(db, schedule_id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule

@router.post("/", response_model=Schedule, status_code=status.HTTP_201_CREATED)
def create_schedule(
    schedule_in: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new schedule.
    
    The schedule will be validated and the next run time will be calculated automatically.
    """
    # Check if schedule with same name already exists
    existing_schedule = schedule_crud.get_by_name(db, name=schedule_in.name)
    if existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule with this name already exists"
        )
    
    schedule = schedule_crud.create(db, obj_in=schedule_in)
    return schedule

@router.put("/{schedule_id}", response_model=Schedule)
def update_schedule(
    schedule_id: int,
    schedule_in: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing schedule.
    
    The next run time will be recalculated if schedule parameters are changed.
    """
    schedule = schedule_crud.get(db, schedule_id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    schedule = schedule_crud.update(db, db_obj=schedule, obj_in=schedule_in)
    return schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a schedule and all its associated device actions."""
    schedule = schedule_crud.get(db, schedule_id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    schedule_crud.remove(db, schedule_id=schedule_id)
    return None

@router.post("/{schedule_id}/enable", response_model=Schedule)
def enable_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enable a schedule."""
    schedule = schedule_crud.get(db, schedule_id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    if schedule.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule is already enabled"
        )
    
    schedule = schedule_crud.update(db, db_obj=schedule, obj_in=ScheduleUpdate(is_enabled=True))
    return schedule

@router.post("/{schedule_id}/disable", response_model=Schedule)
def disable_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disable a schedule."""
    schedule = schedule_crud.get(db, schedule_id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    if not schedule.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule is already disabled"
        )
    
    schedule = schedule_crud.update(db, db_obj=schedule, obj_in=ScheduleUpdate(is_enabled=False))
    return schedule

# Device Action endpoints
@router.get("/device-actions/", response_model=List[DeviceActionWithDevice])
def get_device_actions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    schedule_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all device actions with optional filtering.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **status**: Filter by action status (pending, in_progress, success, failed)
    - **device_id**: Filter actions for a specific device
    - **schedule_id**: Filter actions for a specific schedule
    """
    actions = device_action_crud.get_with_device_info(
        db, skip=skip, limit=limit,
        status=status,
        device_id=device_id,
        schedule_id=schedule_id
    )
    return actions

@router.get("/device-actions/stats", response_model=DeviceActionStats)
def get_device_action_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device action statistics."""
    return device_action_crud.get_stats(db)

@router.get("/device-actions/{action_id}", response_model=DeviceActionWithDevice)
def get_device_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific device action by ID with device information."""
    action = device_action_crud.get(db, action_id=action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device action not found"
        )
    
    # Get device information
    device = db.query(Device).filter(Device.id == action.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated device not found"
        )
    
    # Convert to response format
    action_dict = {
        "id": action.id,
        "schedule_id": action.schedule_id,
        "device_id": action.device_id,
        "action_type": action.action_type,
        "parameters": action.parameters,
        "status": action.status,
        "scheduled_time": action.scheduled_time,
        "executed_time": action.executed_time,
        "result": action.result,
        "error_message": action.error_message,
        "created_at": action.created_at,
        "updated_at": action.updated_at,
        "device": {
            "id": device.id,
            "name": device.name,
            "device_type": device.device_type,
            "unit": device.unit
        }
    }
    
    return action_dict

@router.post("/device-actions/", response_model=DeviceAction, status_code=status.HTTP_201_CREATED)
def create_device_action(
    action_in: DeviceActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new device action.
    
    This can be used to manually create device actions or for testing purposes.
    """
    # Validate that the device exists
    device = db.query(Device).filter(Device.id == action_in.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found"
        )
    
    # Validate that the schedule exists if provided
    if action_in.schedule_id:
        schedule = schedule_crud.get(db, schedule_id=action_in.schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule not found"
            )
    
    action = device_action_crud.create(db, obj_in=action_in)
    return action

@router.put("/device-actions/{action_id}", response_model=DeviceAction)
def update_device_action(
    action_id: int,
    action_in: DeviceActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing device action."""
    action = device_action_crud.get(db, action_id=action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device action not found"
        )
    
    action = device_action_crud.update(db, db_obj=action, obj_in=action_in)
    return action

@router.delete("/device-actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a device action."""
    action = device_action_crud.get(db, action_id=action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device action not found"
        )
    
    device_action_crud.remove(db, action_id=action_id)
    return None

@router.post("/device-actions/{action_id}/execute", response_model=DeviceAction)
def execute_device_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually execute a device action.
    
    This will mark the action as executed immediately, regardless of its scheduled time.
    """
    action = device_action_crud.get(db, action_id=action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device action not found"
        )
    
    if action.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action is not pending (current status: {action.status})"
        )
    
    # Mark as executed
    action = device_action_crud.mark_executed(
        db, action_id=action_id,
        result={"manual_execution": True, "executed_by": current_user.username}
    )
    return action

@router.post("/device-actions/cleanup", status_code=status.HTTP_200_OK)
def cleanup_old_device_actions(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old device actions.
    
    This will delete device actions older than the specified number of days.
    Only successful and failed actions are cleaned up; pending actions are preserved.
    """
    deleted_count = device_action_crud.cleanup_old_actions(db, days=days)
    return {"deleted_count": deleted_count, "days": days}

# Scheduler health endpoint
@router.get("/health", response_model=SchedulerHealth)
def get_scheduler_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get scheduler worker health status.
    
    This endpoint provides information about the scheduler system status,
    including uptime, schedule counts, and next evaluation time.
    """
    # Get schedule statistics
    stats = schedule_crud.get_stats(db)
    
    # Calculate next check time (assuming 30-second intervals)
    current_time = datetime.now(timezone.utc)
    next_check = current_time.replace(second=((current_time.second // 30) + 1) * 30, microsecond=0)
    if next_check <= current_time:
        next_check = next_check.replace(minute=next_check.minute + 1)
    
    return SchedulerHealth(
        status="healthy",  # In a real implementation, check if worker is running
        uptime_seconds=3600.0,  # Placeholder - would be calculated from worker start time
        last_check=current_time,
        total_schedules=stats["total_schedules"],
        next_check=next_check
    ) 