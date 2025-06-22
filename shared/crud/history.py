"""
History CRUD Operations

This module provides database operations for querying historical data
from both the raw history table and the hourly aggregates table.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from shared.db.models import History, HistoryHourlyAggregate, Device


async def get_raw_history(
    session: AsyncSession,
    device_id: int,
    hours: int = 24,
    limit: int = 1000
) -> List[History]:
    """
    Fetch raw historical data for a specific device.
    
    Args:
        session: Database session
        device_id: ID of the device to fetch history for
        hours: Number of hours to look back (default: 24)
        limit: Maximum number of records to return (default: 1000)
        
    Returns:
        List of History records ordered by timestamp (newest first)
    """
    # Calculate the start time based on hours parameter
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Build the query
    query = select(History).where(
        and_(
            History.device_id == device_id,
            History.timestamp >= start_time,
            History.value.is_not(None)  # Only return records with actual values
        )
    ).order_by(desc(History.timestamp)).limit(limit)
    
    result = await session.execute(query)
    return result.scalars().all()


async def get_hourly_history(
    session: AsyncSession,
    device_id: int,
    start_date: str,
    end_date: str
) -> List[HistoryHourlyAggregate]:
    """
    Fetch hourly aggregated historical data for a specific device.
    
    Args:
        session: Database session
        device_id: ID of the device to fetch history for
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        
    Returns:
        List of HistoryHourlyAggregate records ordered by hour_timestamp
    """
    try:
        # Parse the date strings
        start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00")
        end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD format. Error: {e}")
    
    # Build the query
    query = select(HistoryHourlyAggregate).where(
        and_(
            HistoryHourlyAggregate.device_id == device_id,
            HistoryHourlyAggregate.hour_timestamp >= start_datetime,
            HistoryHourlyAggregate.hour_timestamp <= end_datetime
        )
    ).order_by(HistoryHourlyAggregate.hour_timestamp)
    
    result = await session.execute(query)
    return result.scalars().all()


async def get_device_by_id(
    session: AsyncSession,
    device_id: int
) -> Optional[Device]:
    """
    Get a device by its ID.
    
    Args:
        session: Database session
        device_id: ID of the device to fetch
        
    Returns:
        Device object if found, None otherwise
    """
    query = select(Device).where(Device.id == device_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_raw_history_stats(
    session: AsyncSession,
    device_id: int,
    hours: int = 24
) -> dict:
    """
    Get statistics about raw historical data for a device.
    
    Args:
        session: Database session
        device_id: ID of the device
        hours: Number of hours to look back
        
    Returns:
        Dictionary with statistics (count, date_range, etc.)
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Count total records
    count_query = select(History.id).where(
        and_(
            History.device_id == device_id,
            History.timestamp >= start_time,
            History.value.is_not(None)
        )
    )
    count_result = await session.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    # Get date range
    range_query = select(
        History.timestamp
    ).where(
        and_(
            History.device_id == device_id,
            History.timestamp >= start_time,
            History.value.is_not(None)
        )
    ).order_by(History.timestamp)
    
    range_result = await session.execute(range_query)
    timestamps = range_result.scalars().all()
    
    if timestamps:
        earliest = min(timestamps)
        latest = max(timestamps)
    else:
        earliest = None
        latest = None
    
    return {
        "device_id": device_id,
        "total_records": total_count,
        "hours_back": hours,
        "earliest_timestamp": earliest,
        "latest_timestamp": latest,
        "date_range": {
            "start": earliest,
            "end": latest
        } if earliest and latest else None
    }


async def get_hourly_history_stats(
    session: AsyncSession,
    device_id: int,
    start_date: str,
    end_date: str
) -> dict:
    """
    Get statistics about hourly aggregated data for a device.
    
    Args:
        session: Database session
        device_id: ID of the device
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        
    Returns:
        Dictionary with statistics
    """
    try:
        start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00")
        end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD format. Error: {e}")
    
    # Count total records
    count_query = select(HistoryHourlyAggregate.id).where(
        and_(
            HistoryHourlyAggregate.device_id == device_id,
            HistoryHourlyAggregate.hour_timestamp >= start_datetime,
            HistoryHourlyAggregate.hour_timestamp <= end_datetime
        )
    )
    count_result = await session.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    # Get date range
    range_query = select(
        HistoryHourlyAggregate.hour_timestamp
    ).where(
        and_(
            HistoryHourlyAggregate.device_id == device_id,
            HistoryHourlyAggregate.hour_timestamp >= start_datetime,
            HistoryHourlyAggregate.hour_timestamp <= end_datetime
        )
    ).order_by(HistoryHourlyAggregate.hour_timestamp)
    
    range_result = await session.execute(range_query)
    timestamps = range_result.scalars().all()
    
    if timestamps:
        earliest = min(timestamps)
        latest = max(timestamps)
    else:
        earliest = None
        latest = None
    
    return {
        "device_id": device_id,
        "total_hours": total_count,
        "date_range": {
            "start": start_date,
            "end": end_date
        },
        "data_range": {
            "earliest": earliest,
            "latest": latest
        } if earliest and latest else None
    } 