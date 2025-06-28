"""
Lighting Scheduler API endpoints.

This module provides FastAPI endpoints for controlling the lighting scheduler,
including starting, stopping, and monitoring the scheduler.
All operations use the real HAL layer for hardware control.
"""
from datetime import datetime
from typing import Dict, Any
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
from lighting.scheduler.lighting_scheduler import (
    get_lighting_scheduler_service,
    start_lighting_scheduler,
    stop_lighting_scheduler,
    get_lighting_scheduler_status,
    get_lighting_runner
)

logger = get_logger(__name__)

router = APIRouter(prefix="/scheduler", tags=["Lighting Scheduler"])


class SchedulerStartRequest(BaseModel):
    """Request model for starting the scheduler."""
    interval_seconds: int = Field(30, ge=5, le=3600, description="Interval between iterations in seconds")


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_scheduler(
    request: SchedulerStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Start the lighting behavior scheduler.
    
    Args:
        request: Scheduler start request with interval configuration
        
    Returns:
        Start status and configuration
    """
    try:
        service = get_lighting_scheduler_service()
        
        # Check if already running
        if service.get_service_status()["running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lighting scheduler is already running"
            )
        
        # Start scheduler
        await start_lighting_scheduler(request.interval_seconds)
        
        # Log the operation
        logger.info(f"Lighting scheduler started by user {current_user.username} with {request.interval_seconds}s interval")
        
        return {
            "success": True,
            "interval_seconds": request.interval_seconds,
            "message": f"Lighting scheduler started with {request.interval_seconds}s interval",
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting lighting scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error starting scheduler: {str(e)}"
        )


@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_scheduler(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Stop the lighting behavior scheduler.
    
    Returns:
        Stop status
    """
    try:
        service = get_lighting_scheduler_service()
        
        # Check if not running
        if not service.get_service_status()["running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lighting scheduler is not running"
            )
        
        # Stop scheduler
        await stop_lighting_scheduler()
        
        # Log the operation
        logger.info(f"Lighting scheduler stopped by user {current_user.username}")
        
        return {
            "success": True,
            "message": "Lighting scheduler stopped successfully",
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping lighting scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error stopping scheduler: {str(e)}"
        )


@router.get("/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get the lighting scheduler status.
    
    Returns:
        Detailed scheduler status information
    """
    try:
        status_info = get_lighting_scheduler_status()
        
        return {
            "scheduler_status": status_info,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting scheduler status: {str(e)}"
        )


@router.post("/restart", status_code=status.HTTP_200_OK)
async def restart_scheduler(
    request: SchedulerStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Restart the lighting behavior scheduler.
    
    Args:
        request: Scheduler restart request with interval configuration
        
    Returns:
        Restart status and configuration
    """
    try:
        service = get_lighting_scheduler_service()
        
        # Stop if running
        if service.get_service_status()["running"]:
            await stop_lighting_scheduler()
            
        # Start with new configuration
        await start_lighting_scheduler(request.interval_seconds)
        
        # Log the operation
        logger.info(f"Lighting scheduler restarted by user {current_user.username} with {request.interval_seconds}s interval")
        
        return {
            "success": True,
            "interval_seconds": request.interval_seconds,
            "message": f"Lighting scheduler restarted with {request.interval_seconds}s interval",
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting lighting scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error restarting scheduler: {str(e)}"
        )


@router.post("/run-single-iteration", status_code=status.HTTP_200_OK)
async def run_single_iteration(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Run a single iteration of the lighting behavior runner.
    
    This endpoint allows manual execution of the behavior runner
    without affecting the scheduler's automatic operation.
    
    Returns:
        Iteration results
    """
    try:
        runner = get_lighting_runner()
        
        if not runner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lighting runner not available - scheduler may not be started"
            )
        
        # Run single iteration
        intensities = runner.run_iteration()
        
        # Log the operation
        logger.info(f"Single iteration executed by user {current_user.username}: {len(intensities)} channels processed")
        
        return {
            "success": True,
            "channels_processed": len(intensities),
            "intensities": intensities,
            "timestamp": datetime.utcnow(),
            "message": f"Single iteration completed: {len(intensities)} channels processed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running single iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error running iteration: {str(e)}"
        )


@router.get("/runner-status")
async def get_runner_status(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get the lighting behavior runner status.
    
    Returns:
        Runner status information
    """
    try:
        runner = get_lighting_runner()
        
        if not runner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lighting runner not available - scheduler may not be started"
            )
        
        # Get runner status
        registered_channels = runner.get_registered_channels()
        hardware_status = runner.get_hardware_status()
        queue_status = runner.get_queue_status()
        
        return {
            "registered_channels": registered_channels,
            "hardware_status": hardware_status,
            "queue_status": queue_status,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting runner status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting runner status: {str(e)}"
        )


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_scheduler(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Clean up expired effects and overrides.
    
    This endpoint triggers cleanup of expired entries in the scheduler's
    effect and override queues.
    
    Returns:
        Cleanup results
    """
    try:
        runner = get_lighting_runner()
        
        if not runner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lighting runner not available - scheduler may not be started"
            )
        
        # Run cleanup
        cleanup_result = runner.cleanup_expired_entries()
        
        # Log the operation
        total_cleaned = cleanup_result.get("effects_cleaned", 0) + cleanup_result.get("overrides_cleaned", 0)
        logger.info(f"Scheduler cleanup executed by user {current_user.username}: {total_cleaned} entries cleaned")
        
        return {
            "success": True,
            "cleanup_result": cleanup_result,
            "timestamp": datetime.utcnow(),
            "message": f"Cleanup completed: {total_cleaned} entries cleaned"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during scheduler cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during cleanup: {str(e)}"
        ) 