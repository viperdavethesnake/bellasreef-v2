"""
FastAPI endpoints for lighting behavior log management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.schemas.user import User
from hal.deps import get_current_user_or_service

from lighting.services.crud import lighting_behavior_log
from lighting.models.schemas import (
    LightingBehaviorLog,
    LightingBehaviorLogCreate,
    LightingBehaviorLogUpdate,
)

router = APIRouter(prefix="/logs", tags=["lighting-logs"])


@router.get("/", response_model=List[LightingBehaviorLog])
async def get_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    behavior_id: Optional[int] = Query(None, description="Filter by behavior ID"),
    assignment_id: Optional[int] = Query(None, description="Filter by assignment ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    hours: Optional[int] = Query(None, ge=1, le=8760, description="Filter by hours back (1-8760)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehaviorLog]:
    """
    Get lighting behavior logs with optional filtering.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **channel_id**: Filter by specific channel ID
    - **group_id**: Filter by specific group ID
    - **behavior_id**: Filter by specific behavior ID
    - **assignment_id**: Filter by specific assignment ID
    - **status**: Filter by status (active, ended, error, etc.)
    - **hours**: Filter by hours back from current time (1-8760, max 1 year)
    """
    logs = await lighting_behavior_log.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        channel_id=channel_id,
        group_id=group_id,
        behavior_id=behavior_id,
        assignment_id=assignment_id,
        status=status,
        hours=hours,
    )
    return logs


@router.get("/{log_id}", response_model=LightingBehaviorLog)
async def get_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehaviorLog:
    """
    Get a specific lighting behavior log entry by ID.
    
    - **log_id**: The unique identifier of the log entry
    """
    log_entry = await lighting_behavior_log.get(db, log_id=log_id)
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior log entry not found"
        )
    return log_entry


@router.post("/", response_model=LightingBehaviorLog, status_code=status.HTTP_201_CREATED)
async def create_log(
    log_in: LightingBehaviorLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehaviorLog:
    """
    Create a new lighting behavior log entry.
    
    This endpoint is typically used by the lighting system to log behavior
    changes, status updates, and errors. All datetime fields are stored in UTC.
    """
    log_entry = await lighting_behavior_log.create(db, obj_in=log_in)
    return log_entry


@router.patch("/{log_id}", response_model=LightingBehaviorLog)
async def update_log(
    log_id: int,
    log_update: LightingBehaviorLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehaviorLog:
    """
    Update a lighting behavior log entry.
    
    - **log_id**: The unique identifier of the log entry to update
    - **log_update**: The updated log data (only provided fields will be updated)
    
    Note: This endpoint is typically used for administrative purposes to
    add notes or update error information.
    """
    log_entry = await lighting_behavior_log.get(db, log_id=log_id)
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior log entry not found"
        )
    
    updated_log = await lighting_behavior_log.update(db, db_obj=log_entry, obj_in=log_update)
    return updated_log


@router.get("/channel/{channel_id}", response_model=List[LightingBehaviorLog])
async def get_channel_logs(
    channel_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    hours: Optional[int] = Query(None, ge=1, le=8760, description="Filter by hours back (1-8760)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehaviorLog]:
    """
    Get logs for a specific channel.
    
    - **channel_id**: The channel ID to get logs for
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **hours**: Filter by hours back from current time (1-8760, max 1 year)
    """
    logs = await lighting_behavior_log.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        channel_id=channel_id,
        hours=hours,
    )
    return logs


@router.get("/group/{group_id}", response_model=List[LightingBehaviorLog])
async def get_group_logs(
    group_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    hours: Optional[int] = Query(None, ge=1, le=8760, description="Filter by hours back (1-8760)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehaviorLog]:
    """
    Get logs for a specific group.
    
    - **group_id**: The group ID to get logs for
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **hours**: Filter by hours back from current time (1-8760, max 1 year)
    """
    logs = await lighting_behavior_log.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        group_id=group_id,
        hours=hours,
    )
    return logs


@router.get("/behavior/{behavior_id}", response_model=List[LightingBehaviorLog])
async def get_behavior_logs(
    behavior_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    hours: Optional[int] = Query(None, ge=1, le=8760, description="Filter by hours back (1-8760)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehaviorLog]:
    """
    Get logs for a specific behavior.
    
    - **behavior_id**: The behavior ID to get logs for
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **hours**: Filter by hours back from current time (1-8760, max 1 year)
    """
    logs = await lighting_behavior_log.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        behavior_id=behavior_id,
        hours=hours,
    )
    return logs


@router.get("/errors/recent", response_model=List[LightingBehaviorLog])
async def get_recent_errors(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    hours: int = Query(24, ge=1, le=8760, description="Hours to look back (1-8760)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehaviorLog]:
    """
    Get recent error logs.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **hours**: Hours to look back for errors (1-8760, max 1 year)
    """
    logs = await lighting_behavior_log.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        status="error",
        hours=hours,
    )
    return logs 