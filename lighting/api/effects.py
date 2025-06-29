"""
Lighting Effects and Overrides API endpoints.

This module provides FastAPI endpoints for managing lighting effects and overrides,
including adding, removing, and monitoring effects and overrides.
All operations use the real HAL layer for hardware control.
"""
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from shared.db.database import get_db
from shared.schemas.user import User
from shared.utils.logger import get_logger
from shared.api.deps import get_current_user_or_service

from lighting.models.schemas import (
    LightingBehaviorLog,
    LightingBehaviorLogCreate,
)
from lighting.api.runner_instance import get_runner

logger = get_logger(__name__)

router = APIRouter(prefix="/effects", tags=["Lighting Effects & Overrides"])


class EffectCreateRequest(BaseModel):
    """Request model for creating an effect."""
    effect_type: str = Field(..., description="Type of effect to apply")
    channels: List[int] = Field(..., description="List of channel IDs to apply effect to")
    parameters: Dict = Field(default_factory=dict, description="Effect parameters")
    start_time: Optional[datetime] = Field(None, description="When to start the effect (defaults to now)")
    duration_minutes: int = Field(60, description="How long the effect should last")
    priority: int = Field(1, description="Effect priority (higher = more important)")


class OverrideCreateRequest(BaseModel):
    """Request model for creating an override."""
    override_type: str = Field(..., description="Type of override to apply")
    channels: List[int] = Field(..., description="List of channel IDs to apply override to")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Override intensity (0.0-1.0)")
    start_time: Optional[datetime] = Field(None, description="When to start the override (defaults to now)")
    duration_minutes: int = Field(60, description="How long the override should last")
    priority: int = Field(10, description="Override priority (higher = more important)")
    reason: Optional[str] = Field(None, description="Reason for the override")


@router.post("/add", status_code=status.HTTP_200_OK)
async def add_effect(
    request: EffectCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Add an effect to the effect queue.
    
    Args:
        request: Effect creation request
        
    Returns:
        Effect ID and status
    """
    try:
        runner = get_runner()
        
        # Validate channels are registered
        registered_channels = runner.get_registered_channels()
        unregistered_channels = [ch_id for ch_id in request.channels if ch_id not in registered_channels]
        if unregistered_channels:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channels not registered: {unregistered_channels}"
            )
        
        # Add effect through queue manager
        effect_id = runner.queue_manager.add_effect(
            effect_type=request.effect_type,
            channels=request.channels,
            parameters=request.parameters,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            priority=request.priority,
            current_time=datetime.utcnow()
        )
        
        # Log the operation
        logger.info(f"Effect added by user {current_user.username}: {request.effect_type} on channels {request.channels}")
        
        return {
            "success": True,
            "effect_id": effect_id,
            "effect_type": request.effect_type,
            "channels": request.channels,
            "duration_minutes": request.duration_minutes,
            "priority": request.priority,
            "message": f"Effect {request.effect_type} added successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding effect: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error adding effect: {str(e)}"
        )


@router.delete("/{effect_id}/remove", status_code=status.HTTP_200_OK)
async def remove_effect(
    effect_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Remove an effect from the effect queue.
    
    Args:
        effect_id: ID of effect to remove
        
    Returns:
        Removal status
    """
    try:
        runner = get_runner()
        
        # Remove effect through queue manager
        success = runner.queue_manager.remove_effect(effect_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Effect {effect_id} not found"
            )
        
        # Log the operation
        logger.info(f"Effect {effect_id} removed by user {current_user.username}")
        
        return {
            "success": True,
            "effect_id": effect_id,
            "message": f"Effect {effect_id} removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing effect {effect_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error removing effect: {str(e)}"
        )


@router.post("/overrides/add", status_code=status.HTTP_200_OK)
async def add_override(
    request: OverrideCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Add an override to the override queue.
    
    Args:
        request: Override creation request
        
    Returns:
        Override ID and status
    """
    try:
        runner = get_runner()
        
        # Validate channels are registered
        registered_channels = runner.get_registered_channels()
        unregistered_channels = [ch_id for ch_id in request.channels if ch_id not in registered_channels]
        if unregistered_channels:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channels not registered: {unregistered_channels}"
            )
        
        # Add override through queue manager
        override_id = runner.queue_manager.add_override(
            override_type=request.override_type,
            channels=request.channels,
            intensity=request.intensity,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            priority=request.priority,
            reason=request.reason
        )
        
        # Log the operation
        logger.info(f"Override added by user {current_user.username}: {request.override_type} on channels {request.channels}")
        
        return {
            "success": True,
            "override_id": override_id,
            "override_type": request.override_type,
            "channels": request.channels,
            "intensity": request.intensity,
            "duration_minutes": request.duration_minutes,
            "priority": request.priority,
            "reason": request.reason,
            "message": f"Override {request.override_type} added successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding override: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error adding override: {str(e)}"
        )


@router.delete("/overrides/{override_id}/remove", status_code=status.HTTP_200_OK)
async def remove_override(
    override_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Remove an override from the override queue.
    
    Args:
        override_id: ID of override to remove
        
    Returns:
        Removal status
    """
    try:
        runner = get_runner()
        
        # Remove override through queue manager
        success = runner.queue_manager.remove_override(override_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Override {override_id} not found"
            )
        
        # Log the operation
        logger.info(f"Override {override_id} removed by user {current_user.username}")
        
        return {
            "success": True,
            "override_id": override_id,
            "message": f"Override {override_id} removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing override {override_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error removing override: {str(e)}"
        )


@router.get("/list")
async def list_effects_and_overrides(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    List all active effects and overrides.
    
    Returns:
        List of active effects and overrides
    """
    try:
        runner = get_runner()
        current_time = datetime.utcnow()
        
        # Get active effects and overrides
        active_effects = runner.queue_manager.effect_queue.get_active_effects(current_time)
        active_overrides = runner.queue_manager.override_queue.get_active_overrides(current_time)
        
        # Format effects
        effects_list = [
            {
                "effect_id": effect.effect_id,
                "effect_type": effect.effect_type,
                "channels": effect.channels,
                "parameters": effect.parameters,
                "start_time": effect.start_time,
                "duration_minutes": effect.duration_minutes,
                "priority": effect.priority,
                "progress": effect.get_progress(current_time),
                "is_active": effect.is_active(current_time),
            }
            for effect in active_effects
        ]
        
        # Format overrides
        overrides_list = [
            {
                "override_id": override.override_id,
                "override_type": override.override_type,
                "channels": override.channels,
                "intensity": override.get_override_intensity(current_time),
                "start_time": override.start_time,
                "duration_minutes": override.duration_minutes,
                "priority": override.priority,
                "reason": override.reason,
                "progress": override.get_progress(current_time),
                "is_active": override.is_active(current_time),
            }
            for override in active_overrides
        ]
        
        return {
            "current_time": current_time,
            "effects": effects_list,
            "overrides": overrides_list,
            "total_effects": len(effects_list),
            "total_overrides": len(overrides_list),
        }
        
    except Exception as e:
        logger.error(f"Error listing effects and overrides: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error listing effects and overrides: {str(e)}"
        )


@router.get("/channel/{channel_id}/status")
async def get_channel_effects_status(
    channel_id: int,
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get effects and overrides status for a specific channel.
    
    Args:
        channel_id: Channel ID
        
    Returns:
        Channel effects and overrides status
    """
    try:
        runner = get_runner()
        
        # Get channel queue status
        channel_status = runner.queue_manager.get_channel_queue_status(channel_id)
        
        return channel_status
        
    except Exception as e:
        logger.error(f"Error getting channel {channel_id} effects status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting channel effects status: {str(e)}"
        )


@router.post("/clear-all", status_code=status.HTTP_200_OK)
async def clear_all_effects_and_overrides(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Clear all active effects and overrides.
    
    Returns:
        Clear operation status
    """
    try:
        runner = get_runner()
        
        # Get current counts
        current_time = datetime.utcnow()
        active_effects = runner.queue_manager.effect_queue.get_active_effects(current_time)
        active_overrides = runner.queue_manager.override_queue.get_active_overrides(current_time)
        
        # Remove all active effects
        effects_removed = 0
        for effect in active_effects:
            if runner.queue_manager.remove_effect(effect.effect_id):
                effects_removed += 1
        
        # Remove all active overrides
        overrides_removed = 0
        for override in active_overrides:
            if runner.queue_manager.remove_override(override.override_id):
                overrides_removed += 1
        
        # Log the operation
        logger.info(f"All effects and overrides cleared by user {current_user.username}: {effects_removed} effects, {overrides_removed} overrides")
        
        return {
            "success": True,
            "effects_removed": effects_removed,
            "overrides_removed": overrides_removed,
            "message": f"Cleared {effects_removed} effects and {overrides_removed} overrides"
        }
        
    except Exception as e:
        logger.error(f"Error clearing all effects and overrides: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error clearing effects and overrides: {str(e)}"
        ) 