"""
Lighting Runner API endpoints.

This module provides FastAPI endpoints for controlling the lighting behavior runner,
including channel registration, status monitoring, and runner control operations.
All operations use the real HAL layer for hardware control.
"""
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

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

router = APIRouter(prefix="/runner", tags=["Lighting Runner"])


@router.post("/channels/{channel_id}/register", status_code=status.HTTP_200_OK)
async def register_channel(
    channel_id: int,
    controller_address: int,
    channel_number: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Register a lighting channel with the HAL service.
    
    Args:
        channel_id: Lighting system channel identifier
        controller_address: I2C address of the PCA9685 controller (0x40-0x7F)
        channel_number: Channel number on the controller (0-15)
        
    Returns:
        Registration status and channel information
    """
    try:
        runner = get_runner()
        
        # Validate inputs
        if not 0 <= channel_number <= 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel number must be 0-15, got {channel_number}"
            )
        if not 0x40 <= controller_address <= 0x7F:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Controller address must be 0x40-0x7F, got {hex(controller_address)}"
            )
        
        # Register channel
        success = runner.register_channel(channel_id, controller_address, channel_number)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register channel {channel_id}"
            )
        
        # Log the registration
        log_entry = LightingBehaviorLogCreate(
            channel_id=channel_id,
            status="channel_registered",
            notes=f"Channel registered with I2C:{hex(controller_address)} Ch:{channel_number} by user {current_user.username}"
        )
        
        # TODO: Create log entry through behavior manager when available
        logger.info(f"Channel {channel_id} registered: I2C:{hex(controller_address)} Ch:{channel_number}")
        
        return {
            "success": True,
            "channel_id": channel_id,
            "controller_address": hex(controller_address),
            "channel_number": channel_number,
            "message": f"Channel {channel_id} registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering channel {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error registering channel: {str(e)}"
        )


@router.delete("/channels/{channel_id}/unregister", status_code=status.HTTP_200_OK)
async def unregister_channel(
    channel_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Unregister a lighting channel from the HAL service.
    
    Args:
        channel_id: Lighting system channel identifier
        
    Returns:
        Unregistration status
    """
    try:
        runner = get_runner()
        
        # Unregister channel
        success = runner.unregister_channel(channel_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not found or already unregistered"
            )
        
        # Log the unregistration
        logger.info(f"Channel {channel_id} unregistered by user {current_user.username}")
        
        return {
            "success": True,
            "channel_id": channel_id,
            "message": f"Channel {channel_id} unregistered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering channel {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error unregistering channel: {str(e)}"
        )


@router.get("/channels", response_model=List[int])
async def get_registered_channels(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get list of registered channel IDs.
    
    Returns:
        List of registered channel IDs
    """
    try:
        runner = get_runner()
        channels = runner.get_registered_channels()
        return channels
        
    except Exception as e:
        logger.error(f"Error getting registered channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting registered channels: {str(e)}"
        )


@router.get("/channels/{channel_id}/status")
async def get_channel_status(
    channel_id: int,
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get detailed status for a specific channel.
    
    Args:
        channel_id: Channel identifier
        
    Returns:
        Channel status information
    """
    try:
        runner = get_runner()
        status_info = runner.get_channel_status(channel_id)
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting status for channel {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting channel status: {str(e)}"
        )


@router.post("/channels/{channel_id}/intensity", status_code=status.HTTP_200_OK)
async def set_channel_intensity(
    channel_id: int,
    intensity: float,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Set intensity for a specific channel directly.
    
    Args:
        channel_id: Channel identifier
        intensity: Desired intensity (0.0-1.0)
        
    Returns:
        Write status
    """
    try:
        # Validate intensity
        if not 0.0 <= intensity <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Intensity must be 0.0-1.0, got {intensity}"
            )
        
        runner = get_runner()
        
        # Check if channel is registered
        if channel_id not in runner.get_registered_channels():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not registered"
            )
        
        # Write intensity to hardware
        success = runner.hal_service.write_channel_intensity(
            channel_id, 
            intensity, 
            {"user": current_user.username, "api": "set_channel_intensity"}
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write intensity {intensity} to channel {channel_id}"
            )
        
        # Log the operation
        logger.info(f"Channel {channel_id} intensity set to {intensity} by user {current_user.username}")
        
        return {
            "success": True,
            "channel_id": channel_id,
            "intensity": intensity,
            "message": f"Channel {channel_id} intensity set to {intensity}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting intensity for channel {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error setting channel intensity: {str(e)}"
        )


@router.get("/channels/{channel_id}/intensity")
async def get_channel_intensity(
    channel_id: int,
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get current intensity for a specific channel.
    
    Args:
        channel_id: Channel identifier
        
    Returns:
        Current intensity value
    """
    try:
        runner = get_runner()
        
        # Check if channel is registered
        if channel_id not in runner.get_registered_channels():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not registered"
            )
        
        # Read intensity from hardware
        intensity = runner.hal_service.read_channel_intensity(channel_id)
        
        if intensity is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read intensity from channel {channel_id}"
            )
        
        return {
            "channel_id": channel_id,
            "intensity": intensity,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading intensity for channel {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error reading channel intensity: {str(e)}"
        )


@router.post("/channels/bulk-intensity", status_code=status.HTTP_200_OK)
async def set_multiple_channel_intensities(
    channel_intensities: Dict[int, float],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Set intensities for multiple channels efficiently.
    
    Args:
        channel_intensities: Dictionary mapping channel_id to intensity (0.0-1.0)
        
    Returns:
        Write results for each channel
    """
    try:
        # Validate intensities
        for channel_id, intensity in channel_intensities.items():
            if not 0.0 <= intensity <= 1.0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Intensity must be 0.0-1.0 for channel {channel_id}, got {intensity}"
                )
        
        runner = get_runner()
        registered_channels = runner.get_registered_channels()
        
        # Check if all channels are registered
        unregistered_channels = [ch_id for ch_id in channel_intensities.keys() if ch_id not in registered_channels]
        if unregistered_channels:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channels not registered: {unregistered_channels}"
            )
        
        # Write intensities to hardware
        results = runner.hal_service.write_multiple_channels(
            channel_intensities,
            {"user": current_user.username, "api": "set_multiple_channel_intensities"}
        )
        
        # Log the operation
        successful_writes = sum(1 for success in results.values() if success)
        failed_writes = len(results) - successful_writes
        
        logger.info(f"Bulk intensity write: {successful_writes} successful, {failed_writes} failed by user {current_user.username}")
        
        return {
            "success": True,
            "total_channels": len(channel_intensities),
            "successful_writes": successful_writes,
            "failed_writes": failed_writes,
            "results": results,
            "message": f"Bulk intensity write completed: {successful_writes} successful, {failed_writes} failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk intensity write: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error in bulk intensity write: {str(e)}"
        )


@router.post("/run-iteration", status_code=status.HTTP_200_OK)
async def run_iteration(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Run a single iteration of the lighting behavior runner.
    
    This endpoint triggers the runner to:
    1. Fetch active behavior assignments
    2. Compute desired intensities
    3. Apply effects and overrides
    4. Write to hardware through HAL
    
    Returns:
        Iteration results and statistics
    """
    try:
        runner = get_runner()
        
        # Run iteration
        intensities = runner.run_iteration()
        
        # Log the operation
        logger.info(f"Runner iteration executed by user {current_user.username}: {len(intensities)} channels processed")
        
        return {
            "success": True,
            "channels_processed": len(intensities),
            "intensities": intensities,
            "timestamp": datetime.utcnow(),
            "message": f"Runner iteration completed: {len(intensities)} channels processed"
        }
        
    except Exception as e:
        logger.error(f"Error running iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error running iteration: {str(e)}"
        )


@router.get("/hardware-status")
async def get_hardware_status(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get hardware status information.
    
    Returns:
        Hardware status including registered channels and manager status
    """
    try:
        runner = get_runner()
        status_info = runner.get_hardware_status()
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting hardware status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting hardware status: {str(e)}"
        )


@router.get("/queue-status")
async def get_queue_status(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get current status of effect and override queues.
    
    Returns:
        Queue status information
    """
    try:
        runner = get_runner()
        queue_status = runner.get_queue_status()
        return queue_status
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting queue status: {str(e)}"
        )


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_expired_entries(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Clean up expired effects and overrides.
    
    Returns:
        Cleanup statistics
    """
    try:
        runner = get_runner()
        cleanup_result = runner.cleanup_expired_entries()
        
        # Log the operation
        total_cleaned = cleanup_result.get("effects_cleaned", 0) + cleanup_result.get("overrides_cleaned", 0)
        logger.info(f"Cleanup executed by user {current_user.username}: {total_cleaned} entries cleaned")
        
        return {
            "success": True,
            "cleanup_result": cleanup_result,
            "timestamp": datetime.utcnow(),
            "message": f"Cleanup completed: {total_cleaned} entries cleaned"
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during cleanup: {str(e)}"
        ) 