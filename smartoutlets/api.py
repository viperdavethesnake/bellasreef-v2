"""
SmartOutlet API Routes

This module defines FastAPI routes for smart outlet operations.
"""

from uuid import uuid4
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import async_session
from shared.utils.logger import get_logger
from .manager import SmartOutletManager
from .models import SmartOutlet
from .schemas import SmartOutletCreate, SmartOutletRead, SmartOutletState, SmartOutletUpdate
from .exceptions import OutletNotFoundError, OutletConnectionError
from .handlers import register_exception_handlers

router = APIRouter()


async def get_smart_outlet_manager() -> SmartOutletManager:
    """FastAPI dependency to provide SmartOutletManager instance."""
    logger = get_logger(__name__)
    return SmartOutletManager(async_session, logger)


@router.post("/outlets/", response_model=SmartOutletRead, status_code=status.HTTP_201_CREATED)
async def create_outlet(
    outlet_data: SmartOutletCreate,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    session: AsyncSession = Depends(async_session)
):
    """
    Create a new smart outlet.
    
    Args:
        outlet_data: Smart outlet creation data
        manager: SmartOutletManager instance
        session: Database session
        
    Returns:
        SmartOutletRead: Created outlet data
        
    Raises:
        HTTPException: If outlet with same driver_type and driver_device_id already exists
    """
    # Check for uniqueness constraint
    existing_outlet = await session.execute(
        select(SmartOutlet).where(
            SmartOutlet.driver_type == outlet_data.driver_type.value,
            SmartOutlet.driver_device_id == outlet_data.driver_device_id
        )
    )
    
    if existing_outlet.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Outlet with driver_type '{outlet_data.driver_type.value}' and driver_device_id '{outlet_data.driver_device_id}' already exists"
        )
    
    # Create new outlet
    outlet = SmartOutlet(
        id=uuid4(),
        driver_type=outlet_data.driver_type.value,
        driver_device_id=outlet_data.driver_device_id,
        name=outlet_data.name,
        nickname=outlet_data.nickname,
        ip_address=outlet_data.ip_address,
        auth_info=outlet_data.auth_info,
        location=outlet_data.location,
        role=outlet_data.role.value,
        enabled=outlet_data.enabled,
        poller_enabled=outlet_data.poller_enabled,
        scheduler_enabled=outlet_data.scheduler_enabled
    )
    
    session.add(outlet)
    await session.commit()
    await session.refresh(outlet)
    
    # Register outlet with manager
    try:
        await manager.register_outlet_from_db(outlet.id)
    except Exception as e:
        # Log error but don't fail the creation
        pass
    
    return SmartOutletRead.model_validate(outlet)


@router.get("/outlets/", response_model=List[SmartOutletRead])
async def list_outlets(
    include_disabled: bool = Query(False, description="Include disabled outlets"),
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    List all smart outlets.
    
    Args:
        include_disabled: Whether to include disabled outlets
        manager: SmartOutletManager instance
        
    Returns:
        List[SmartOutletRead]: List of outlet data
    """
    outlets = await manager.get_all_outlets(include_disabled=include_disabled)
    return [SmartOutletRead.model_validate(outlet) for outlet in outlets]


@router.patch("/outlets/{outlet_id}", response_model=SmartOutletRead, status_code=status.HTTP_200_OK)
async def update_outlet(
    outlet_id: str,
    update_data: SmartOutletUpdate,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Update an existing smart outlet configuration.
    
    Args:
        outlet_id: The ID of the outlet to update
        update_data: Update data containing allowed fields
        manager: SmartOutletManager instance
        
    Returns:
        SmartOutletRead: Updated outlet data
    """
    return await manager.update_outlet(outlet_id, update_data)


@router.get("/outlets/{outlet_id}/state", response_model=SmartOutletState)
async def get_outlet_state(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Get the current state of a smart outlet.
    
    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        
    Returns:
        SmartOutletState: Current outlet state
    """
    return await manager.get_outlet_status(outlet_id)


@router.post("/outlets/{outlet_id}/turn_on", status_code=status.HTTP_200_OK)
async def turn_on_outlet(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Turn on a smart outlet.
    
    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        
    Returns:
        dict: Success response
    """
    success = await manager.turn_on_outlet(outlet_id)
    if success:
        return {"message": f"Successfully turned on outlet {outlet_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to turn on outlet {outlet_id}"
        )


@router.post("/outlets/{outlet_id}/turn_off", status_code=status.HTTP_200_OK)
async def turn_off_outlet(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Turn off a smart outlet.
    
    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        
    Returns:
        dict: Success response
    """
    success = await manager.turn_off_outlet(outlet_id)
    if success:
        return {"message": f"Successfully turned off outlet {outlet_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to turn off outlet {outlet_id}"
        )


@router.post("/outlets/{outlet_id}/toggle", response_model=SmartOutletState)
async def toggle_outlet(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Toggle a smart outlet (turn off if on, turn on if off).
    
    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        
    Returns:
        SmartOutletState: Current outlet state after toggle
    """
    success = await manager.toggle_outlet(outlet_id)
    if success:
        # Return the current state after toggle
        return await manager.get_outlet_status(outlet_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle outlet {outlet_id}"
        ) 