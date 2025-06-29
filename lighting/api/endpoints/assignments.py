"""
FastAPI endpoints for lighting behavior assignment management.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from shared.db.database import get_db
from shared.schemas.user import User
from shared.api.deps import get_current_user_or_service

from lighting.services.crud import lighting_behavior_assignment, lighting_behavior, lighting_group, lighting_behavior_log
from lighting.services.behavior_manager import lighting_behavior_manager
from lighting.models.schemas import (
    LightingBehaviorAssignment,
    LightingBehaviorAssignmentCreate,
    LightingBehaviorAssignmentUpdate,
)

router = APIRouter(prefix="/assignments", tags=["lighting-assignments"])


@router.get("/", response_model=List[LightingBehaviorAssignment])
async def get_assignments(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    behavior_id: Optional[int] = Query(None, description="Filter by behavior ID"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehaviorAssignment]:
    """
    Get all lighting behavior assignments with optional filtering.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **channel_id**: Filter by specific channel ID
    - **group_id**: Filter by specific group ID
    - **behavior_id**: Filter by specific behavior ID
    - **active**: Filter by active status
    """
    assignments = await lighting_behavior_assignment.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        channel_id=channel_id,
        group_id=group_id,
        behavior_id=behavior_id,
        active=active,
    )
    return assignments


@router.get("/{assignment_id}", response_model=LightingBehaviorAssignment)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehaviorAssignment:
    """
    Get a specific lighting behavior assignment by ID.
    
    - **assignment_id**: The unique identifier of the assignment
    """
    assignment = await lighting_behavior_assignment.get(db, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior assignment not found"
        )
    return assignment


@router.get("/channel/{channel_id}", response_model=Optional[LightingBehaviorAssignment])
async def get_channel_assignment(
    channel_id: int,
    active_only: bool = Query(True, description="Return only active assignments"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Optional[LightingBehaviorAssignment]:
    """
    Get the current assignment for a specific channel.
    
    - **channel_id**: The channel ID to get assignment for
    - **active_only**: Whether to return only active assignments (default: True)
    """
    assignment = await lighting_behavior_assignment.get_by_channel(
        db, channel_id=channel_id, active_only=active_only
    )
    return assignment


@router.get("/group/{group_id}", response_model=List[LightingBehaviorAssignment])
async def get_group_assignments(
    group_id: int,
    active_only: bool = Query(True, description="Return only active assignments"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehaviorAssignment]:
    """
    Get all assignments for a specific group.
    
    - **group_id**: The group ID to get assignments for
    - **active_only**: Whether to return only active assignments (default: True)
    """
    assignments = await lighting_behavior_assignment.get_by_group(
        db, group_id=group_id, active_only=active_only
    )
    return assignments


@router.post("/", response_model=LightingBehaviorAssignment, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_in: LightingBehaviorAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehaviorAssignment:
    """
    Create a new lighting behavior assignment.
    
    Assigns a behavior to either a channel or a group. Only one active assignment
    per channel is allowed. All datetime fields are stored in UTC.
    
    The system will automatically deactivate any existing active assignments
    for the same channel/group and log all changes.
    """
    # Validate that the behavior exists
    behavior = await lighting_behavior.get(db, behavior_id=assignment_in.behavior_id)
    if not behavior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior not found"
        )
    
    # Validate that the group exists if group_id is provided
    if assignment_in.group_id:
        group = await lighting_group.get(db, group_id=assignment_in.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lighting group not found"
            )
    
    # TODO: Validate that the channel exists when channel table is available
    # For now, we assume the channel_id is valid
    
    # Create assignment with automatic conflict resolution and logging
    assignment = await lighting_behavior_assignment.create(
        db, obj_in=assignment_in, log_crud=lighting_behavior_log
    )
    return assignment


@router.patch("/{assignment_id}", response_model=LightingBehaviorAssignment)
async def update_assignment(
    assignment_id: int,
    assignment_update: LightingBehaviorAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehaviorAssignment:
    """
    Update a lighting behavior assignment.
    
    - **assignment_id**: The unique identifier of the assignment to update
    - **assignment_update**: The updated assignment data (only provided fields will be updated)
    
    All changes are logged automatically.
    """
    assignment = await lighting_behavior_assignment.get(db, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior assignment not found"
        )
    
    # Validate that the behavior exists if behavior_id is being updated
    if assignment_update.behavior_id:
        behavior = await lighting_behavior.get(db, behavior_id=assignment_update.behavior_id)
        if not behavior:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lighting behavior not found"
            )
    
    # Validate that the group exists if group_id is being updated
    if assignment_update.group_id:
        group = await lighting_group.get(db, group_id=assignment_update.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lighting group not found"
            )
    
    updated_assignment = await lighting_behavior_assignment.update(
        db, db_obj=assignment, obj_in=assignment_update, log_crud=lighting_behavior_log
    )
    return updated_assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> None:
    """
    Delete a lighting behavior assignment.
    
    - **assignment_id**: The unique identifier of the assignment to delete
    
    The deletion is logged automatically.
    """
    assignment = await lighting_behavior_assignment.get(db, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior assignment not found"
        )
    
    await lighting_behavior_assignment.remove(
        db, assignment_id=assignment_id, log_crud=lighting_behavior_log
    )
    return None


@router.post("/channel/{channel_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_channel_assignments(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> dict:
    """
    Deactivate all assignments for a specific channel.
    
    - **channel_id**: The channel ID to deactivate assignments for
    
    Returns the number of assignments that were deactivated.
    All deactivations are logged automatically.
    """
    # TODO: Validate that the channel exists when channel table is available
    
    deactivated_assignments = await lighting_behavior_assignment.deactivate_channel_assignments(
        db, channel_id=channel_id, log_crud=lighting_behavior_log
    )
    return {"deactivated_count": len(deactivated_assignments)}


# High-level assignment endpoints using the behavior manager
@router.post("/channel/{channel_id}/assign/{behavior_id}", response_model=Dict[str, Any])
async def assign_behavior_to_channel(
    channel_id: int,
    behavior_id: int,
    start_time: Optional[datetime] = Query(None, description="Assignment start time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="Assignment end time (UTC)"),
    notes: Optional[str] = Query(None, description="Assignment notes"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Dict[str, Any]:
    """
    Assign a behavior to a channel using the behavior manager.
    
    This endpoint provides a higher-level interface for behavior assignment
    with automatic conflict resolution and comprehensive logging.
    
    - **channel_id**: The channel to assign the behavior to
    - **behavior_id**: The behavior to assign
    - **start_time**: Optional start time for the assignment
    - **end_time**: Optional end time for the assignment
    - **notes**: Optional notes about the assignment
    """
    try:
        result = await lighting_behavior_manager.assign_behavior_to_channel(
            db=db,
            channel_id=channel_id,
            behavior_id=behavior_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/group/{group_id}/assign/{behavior_id}", response_model=Dict[str, Any])
async def assign_behavior_to_group(
    group_id: int,
    behavior_id: int,
    start_time: Optional[datetime] = Query(None, description="Assignment start time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="Assignment end time (UTC)"),
    notes: Optional[str] = Query(None, description="Assignment notes"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Dict[str, Any]:
    """
    Assign a behavior to a group using the behavior manager.
    
    This endpoint provides a higher-level interface for group behavior assignment
    with automatic conflict resolution and comprehensive logging.
    
    - **group_id**: The group to assign the behavior to
    - **behavior_id**: The behavior to assign
    - **start_time**: Optional start time for the assignment
    - **end_time**: Optional end time for the assignment
    - **notes**: Optional notes about the assignment
    """
    try:
        result = await lighting_behavior_manager.assign_behavior_to_group(
            db=db,
            group_id=group_id,
            behavior_id=behavior_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/channel/{channel_id}/status", response_model=Dict[str, Any])
async def get_channel_status(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Dict[str, Any]:
    """
    Get the current status of a channel including active assignment and any overrides/effects.
    
    - **channel_id**: The channel ID to get status for
    
    TODO: This will show current assignment, overrides, effects, and calculated output
    when those features are implemented.
    """
    try:
        status = await lighting_behavior_manager.get_channel_status(db, channel_id=channel_id)
        return status
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/group/{group_id}/status", response_model=Dict[str, Any])
async def get_group_status(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Dict[str, Any]:
    """
    Get the current status of a group including all channel assignments.
    
    - **group_id**: The group ID to get status for
    
    TODO: This will show status for all channels in the group when channel
    relationships are implemented.
    """
    try:
        status = await lighting_behavior_manager.get_group_status(db, group_id=group_id)
        return status
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# TODO: Add override and effect endpoints
@router.post("/override", response_model=Dict[str, Any])
async def create_override_assignment(
    channel_id: int,
    behavior_id: int,
    duration_minutes: int = Query(..., ge=1, le=1440, description="Override duration in minutes (1-1440)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Dict[str, Any]:
    """
    Create a temporary override assignment.
    
    - **channel_id**: The channel to override
    - **behavior_id**: The behavior to use for the override
    - **duration_minutes**: How long the override should last (1-1440 minutes)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Override functionality not yet implemented"
    )


@router.post("/effect", response_model=Dict[str, Any])
async def create_effect_assignment(
    channel_id: int,
    effect_type: str = Query(..., description="Type of effect (lightning, storm, etc.)"),
    duration_minutes: int = Query(..., ge=1, le=60, description="Effect duration in minutes (1-60)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Dict[str, Any]:
    """
    Create a temporary effect assignment.
    
    TODO: Implement effect functionality that allows temporary effects
    to be queued and executed without affecting the underlying assignment.
    
    - **channel_id**: The channel to apply the effect to
    - **effect_type**: The type of effect to apply
    - **duration_minutes**: How long the effect should last (1-60 minutes)
    """
    # TODO: Implement effect logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Effect functionality not yet implemented"
    )


@router.get("/preview/{behavior_id}", response_model=Dict[str, Any])
async def preview_behavior(
    behavior_id: int,
    channel_id: Optional[int] = Query(None, description="Channel ID for preview"),
    group_id: Optional[int] = Query(None, description="Group ID for preview"),
    preview_time: Optional[datetime] = Query(None, description="Time to preview (UTC)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> Dict[str, Any]:
    """
    Preview what a behavior would do at a given time.
    
    TODO: Implement behavior preview logic that shows what the behavior
    would output for the given channel/group at the specified time.
    This does not affect any actual assignments.
    
    - **behavior_id**: The behavior to preview
    - **channel_id**: Optional channel ID for preview
    - **group_id**: Optional group ID for preview
    - **preview_time**: Optional time to preview (defaults to current time)
    """
    # Validate that the behavior exists
    behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
    if not behavior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior not found"
        )
    
    # Validate that either channel_id or group_id is provided, but not both
    if channel_id is not None and group_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot preview for both channel and group simultaneously"
        )
    
    if channel_id is None and group_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either channel_id or group_id must be provided"
        )
    
    # TODO: Validate that the channel/group exists when those tables are available
    
    try:
        if channel_id:
            preview_data = await lighting_behavior_manager.preview_behavior_for_channel(
                db=db,
                behavior_id=behavior_id,
                channel_id=channel_id,
                preview_time=preview_time
            )
        else:
            preview_data = await lighting_behavior_manager.preview_behavior_for_group(
                db=db,
                behavior_id=behavior_id,
                group_id=group_id,
                preview_time=preview_time
            )
        
        return preview_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{assignment_id}/weather", response_model=Dict[str, Any])
async def get_assignment_weather(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
):
    """
    Gets the real-time weather conditions for an active LocationBased behavior assignment,
    which can be used to display the current weather's influence on the lighting.
    """
    try:
        weather_status = await lighting_behavior_manager.get_weather_for_assignment(db, assignment_id=assignment_id)
        return weather_status
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) 