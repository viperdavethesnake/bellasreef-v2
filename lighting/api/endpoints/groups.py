"""
FastAPI endpoints for lighting group management.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.schemas.user import User
from shared.api.deps import get_current_user_or_service

from lighting.services.crud import lighting_group
from lighting.models.schemas import (
    LightingGroup,
    LightingGroupCreate,
    LightingGroupUpdate,
)

router = APIRouter(prefix="/groups", tags=["lighting-groups"])


@router.get("/", response_model=List[LightingGroup])
async def get_groups(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> List[LightingGroup]:
    """
    Get all lighting groups.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    """
    groups = await lighting_group.get_multi(db=db, skip=skip, limit=limit)
    return groups


@router.get("/{group_id}", response_model=LightingGroup)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingGroup:
    """
    Get a specific lighting group by ID.
    
    - **group_id**: The unique identifier of the group
    """
    group = await lighting_group.get(db, group_id=group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting group not found"
        )
    return group


@router.post("/", response_model=LightingGroup, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_in: LightingGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingGroup:
    """
    Create a new lighting group.
    
    Groups can be used to organize lighting channels and assign behaviors
    to multiple channels at once.
    """
    # Check if group with same name already exists
    existing_group = await lighting_group.get_by_name(db, name=group_in.name)
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group with name '{group_in.name}' already exists"
        )
    
    group = await lighting_group.create(db, obj_in=group_in)
    return group


@router.patch("/{group_id}", response_model=LightingGroup)
async def update_group(
    group_id: int,
    group_update: LightingGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> LightingGroup:
    """
    Update a lighting group.
    
    - **group_id**: The unique identifier of the group to update
    - **group_update**: The updated group data (only provided fields will be updated)
    """
    group = await lighting_group.get(db, group_id=group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting group not found"
        )
    
    # Check if name is being updated and if it conflicts with existing group
    if group_update.name and group_update.name != group.name:
        existing_group = await lighting_group.get_by_name(db, name=group_update.name)
        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Group with name '{group_update.name}' already exists"
            )
    
    updated_group = await lighting_group.update(db, db_obj=group, obj_in=group_update)
    return updated_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service),
) -> None:
    """
    Delete a lighting group.
    
    - **group_id**: The unique identifier of the group to delete
    
    Note: This will permanently delete the group. Any assignments to this group
    will need to be handled separately.
    """
    group = await lighting_group.get(db, group_id=group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lighting group not found"
        )
    
    await lighting_group.remove(db, group_id=group_id)
    return None 