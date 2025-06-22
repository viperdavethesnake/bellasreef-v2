"""
History API Router

This module provides endpoints for querying historical data from both
raw history and hourly aggregates tables for any device in the system.
"""

from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.crud.history import (
    get_raw_history,
    get_hourly_history,
    get_device_by_id,
    get_raw_history_stats,
    get_hourly_history_stats
)
from shared.db.models import History, HistoryHourlyAggregate
from shared.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{device_id}/raw", response_model=List[dict])
async def get_device_raw_history(
    device_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back (1-168)"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Maximum records to return"),
    session: AsyncSession = Depends(get_db)
):
    """
    Get raw, high-resolution historical data for a device.
    
    This endpoint fetches the raw data points from the history table,
    perfect for creating detailed, zoomable charts of recent data.
    
    Args:
        device_id: ID of the device
        hours: Number of hours to look back (default: 24, max: 168)
        limit: Maximum number of records to return (default: 1000, max: 10000)
        
    Returns:
        List of raw history records with timestamp and value
    """
    # Verify device exists
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
    
    try:
        # Get raw history data
        history_records = await get_raw_history(session, device_id, hours, limit)
        
        # Convert to response format
        response_data = []
        for record in history_records:
            response_data.append({
                "id": record.id,
                "device_id": record.device_id,
                "timestamp": record.timestamp,
                "value": record.value,
                "json_value": record.json_value,
                "history_metadata": record.history_metadata
            })
        
        logger.info(f"Retrieved {len(response_data)} raw history records for device {device_id}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error fetching raw history for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/hourly", response_model=List[dict])
async def get_device_hourly_history(
    device_id: int,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    session: AsyncSession = Depends(get_db)
):
    """
    Get hourly aggregated historical data for a device.
    
    This endpoint fetches pre-calculated hourly averages from the
    history_hourly_aggregates table, perfect for long-term trend analysis.
    
    Args:
        device_id: ID of the device
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of hourly aggregated records with avg, min, max, and sample count
    """
    # Verify device exists
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
    
    try:
        # Validate date format
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid date format. Use YYYY-MM-DD format (e.g., 2025-06-22)"
            )
        
        # Get hourly history data
        hourly_records = await get_hourly_history(session, device_id, start_date, end_date)
        
        # Convert to response format
        response_data = []
        for record in hourly_records:
            response_data.append({
                "id": record.id,
                "device_id": record.device_id,
                "hour_timestamp": record.hour_timestamp,
                "avg_value": record.avg_value,
                "min_value": record.min_value,
                "max_value": record.max_value,
                "sample_count": record.sample_count,
                "created_at": record.created_at
            })
        
        logger.info(f"Retrieved {len(response_data)} hourly history records for device {device_id}")
        return response_data
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching hourly history for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/raw/stats")
async def get_device_raw_history_stats(
    device_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
    session: AsyncSession = Depends(get_db)
):
    """
    Get statistics about raw historical data for a device.
    
    Args:
        device_id: ID of the device
        hours: Number of hours to look back
        
    Returns:
        Statistics about the raw history data
    """
    # Verify device exists
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
    
    try:
        stats = await get_raw_history_stats(session, device_id, hours)
        return stats
    except Exception as e:
        logger.error(f"Error fetching raw history stats for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/hourly/stats")
async def get_device_hourly_history_stats(
    device_id: int,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    session: AsyncSession = Depends(get_db)
):
    """
    Get statistics about hourly aggregated data for a device.
    
    Args:
        device_id: ID of the device
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Statistics about the hourly history data
    """
    # Verify device exists
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
    
    try:
        # Validate date format
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid date format. Use YYYY-MM-DD format (e.g., 2025-06-22)"
            )
        
        stats = await get_hourly_history_stats(session, device_id, start_date, end_date)
        return stats
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching hourly history stats for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 