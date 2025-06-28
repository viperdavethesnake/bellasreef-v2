"""
FastAPI endpoints for lighting behavior management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.schemas.user import User
from hal.deps import get_current_user_or_service

from lighting.services.crud import lighting_behavior
from lighting.models.schemas import (
    LightingBehavior,
    LightingBehaviorCreate,
    LightingBehaviorUpdate,
)

router = APIRouter(prefix="/behaviors", tags=["lighting-behaviors"])


@router.get("/", response_model=List[LightingBehavior])
async def get_behaviors(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    behavior_type: Optional[str] = Query(None, description="Filter by behavior type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingBehavior]:
    """
    Get all lighting behaviors with optional filtering.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **behavior_type**: Filter by behavior type (Fixed, Diurnal, Lunar, etc.)
    - **enabled**: Filter by enabled status
    """
    behaviors = await lighting_behavior.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        behavior_type=behavior_type,
        enabled=enabled,
    )
    return behaviors


@router.get("/{behavior_id}", response_model=LightingBehavior)
async def get_behavior(
    behavior_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehavior:
    """
    Get a specific lighting behavior by ID.
    
    - **behavior_id**: The unique identifier of the behavior
    """
    behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
    if not behavior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior not found"
        )
    return behavior


@router.post("/", response_model=LightingBehavior, status_code=status.HTTP_201_CREATED)
async def create_behavior(
    behavior_in: LightingBehaviorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehavior:
    """
    Create a new lighting behavior.
    
    The behavior will be created with the specified configuration and can be
    enabled/disabled as needed. All datetime fields are stored in UTC.
    """
    # Check if behavior with same name already exists
    existing_behavior = await lighting_behavior.get_by_name(db, name=behavior_in.name)
    if existing_behavior:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Behavior with name '{behavior_in.name}' already exists"
        )
    
    behavior = await lighting_behavior.create(db, obj_in=behavior_in)
    return behavior


@router.patch("/{behavior_id}", response_model=LightingBehavior)
async def update_behavior(
    behavior_id: int,
    behavior_update: LightingBehaviorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingBehavior:
    """
    Update a lighting behavior.
    
    - **behavior_id**: The unique identifier of the behavior to update
    - **behavior_update**: The updated behavior data (only provided fields will be updated)
    """
    behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
    if not behavior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior not found"
        )
    
    # Check if name is being updated and if it conflicts with existing behavior
    if behavior_update.name and behavior_update.name != behavior.name:
        existing_behavior = await lighting_behavior.get_by_name(db, name=behavior_update.name)
        if existing_behavior:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Behavior with name '{behavior_update.name}' already exists"
            )
    
    updated_behavior = await lighting_behavior.update(db, db_obj=behavior, obj_in=behavior_update)
    return updated_behavior


@router.delete("/{behavior_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_behavior(
    behavior_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> None:
    """
    Delete a lighting behavior.
    
    - **behavior_id**: The unique identifier of the behavior to delete
    
    Note: This will permanently delete the behavior. Consider deactivating instead
    if the behavior might be needed in the future.
    """
    behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
    if not behavior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting behavior not found"
        )
    
    await lighting_behavior.remove(db, behavior_id=behavior_id)
    return None 