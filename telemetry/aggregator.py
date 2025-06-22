#!/usr/bin/env python3
"""
Telemetry Aggregator Worker

This worker implements the "Roll-up and Prune" strategy:
1. Runs periodically (every hour) to aggregate raw history data
2. Calculates hourly averages, min, max, and sample counts
3. Stores results in history_hourly_aggregates table
4. Prunes the processed raw data to keep history table small

The worker processes data from the previous hour to ensure all data points
are captured before aggregation.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from shared.core.config import settings
from shared.db.database import async_session
from shared.db.models import History, HistoryHourlyAggregate
from shared.utils.logger import get_logger
from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class TelemetryAggregator:
    """Worker for aggregating telemetry data and pruning raw history."""
    
    def __init__(self):
        self.logger = logger
    
    async def get_aggregation_time_range(self) -> tuple[datetime, datetime]:
        """
        Calculate the time range for the previous hour.
        
        Returns:
            tuple: (start_time, end_time) for the previous hour
        """
        now = datetime.utcnow()
        # Round down to the nearest hour
        end_time = now.replace(minute=0, second=0, microsecond=0)
        # Previous hour
        start_time = end_time - timedelta(hours=1)
        
        self.logger.info(f"Aggregation time range: {start_time} to {end_time}")
        return start_time, end_time
    
    async def aggregate_hourly_data(self, session: AsyncSession, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Execute the aggregation query to calculate hourly statistics.
        
        Args:
            session: Database session
            start_time: Start of the hour to aggregate
            end_time: End of the hour to aggregate
            
        Returns:
            List of aggregated data records
        """
        query = text("""
            SELECT
                device_id,
                date_trunc('hour', timestamp) AS hour_timestamp,
                AVG(value) AS avg_value,
                MIN(value) AS min_value,
                MAX(value) AS max_value,
                COUNT(id) AS sample_count
            FROM
                history
            WHERE
                timestamp >= :start_time 
                AND timestamp < :end_time
                AND value IS NOT NULL
            GROUP BY
                device_id, hour_timestamp
            ORDER BY
                device_id, hour_timestamp
        """)
        
        result = await session.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        })
        
        aggregates = []
        for row in result:
            aggregates.append({
                "device_id": row.device_id,
                "hour_timestamp": row.hour_timestamp,
                "avg_value": float(row.avg_value),
                "min_value": float(row.min_value),
                "max_value": float(row.max_value),
                "sample_count": row.sample_count
            })
        
        self.logger.info(f"Generated {len(aggregates)} hourly aggregates")
        return aggregates
    
    async def save_aggregates(self, session: AsyncSession, aggregates: List[Dict[str, Any]]) -> int:
        """
        Save aggregated data to the history_hourly_aggregates table.
        
        Args:
            session: Database session
            aggregates: List of aggregated data records
            
        Returns:
            Number of records saved
        """
        if not aggregates:
            self.logger.info("No aggregates to save")
            return 0
        
        # Use INSERT ... ON CONFLICT DO UPDATE to handle duplicates
        insert_query = text("""
            INSERT INTO history_hourly_aggregates 
                (device_id, hour_timestamp, avg_value, min_value, max_value, sample_count)
            VALUES 
                (:device_id, :hour_timestamp, :avg_value, :min_value, :max_value, :sample_count)
            ON CONFLICT (device_id, hour_timestamp) 
            DO UPDATE SET
                avg_value = EXCLUDED.avg_value,
                min_value = EXCLUDED.min_value,
                max_value = EXCLUDED.max_value,
                sample_count = EXCLUDED.sample_count,
                created_at = NOW()
        """)
        
        saved_count = 0
        for aggregate in aggregates:
            await session.execute(insert_query, aggregate)
            saved_count += 1
        
        await session.commit()
        self.logger.info(f"Saved {saved_count} hourly aggregates")
        return saved_count
    
    async def prune_raw_data(self, session: AsyncSession, start_time: datetime, end_time: datetime) -> int:
        """
        Delete the raw data that has been successfully aggregated.
        
        Args:
            session: Database session
            start_time: Start of the time range to prune
            end_time: End of the time range to prune
            
        Returns:
            Number of records deleted
        """
        delete_query = text("""
            DELETE FROM history 
            WHERE timestamp >= :start_time 
            AND timestamp < :end_time
        """)
        
        result = await session.execute(delete_query, {
            "start_time": start_time,
            "end_time": end_time
        })
        
        await session.commit()
        deleted_count = result.rowcount
        self.logger.info(f"Pruned {deleted_count} raw history records")
        return deleted_count
    
    async def run_aggregation_cycle(self) -> bool:
        """
        Run a complete aggregation cycle for the previous hour.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            start_time, end_time = await self.get_aggregation_time_range()
            
            async with async_session() as session:
                # Step 1: Aggregate the data
                self.logger.info("Starting hourly data aggregation...")
                aggregates = await self.aggregate_hourly_data(session, start_time, end_time)
                
                if not aggregates:
                    self.logger.info("No data to aggregate for this time period")
                    return True
                
                # Step 2: Save the aggregates
                self.logger.info("Saving hourly aggregates...")
                saved_count = await self.save_aggregates(session, aggregates)
                
                # Step 3: Prune the raw data
                self.logger.info("Pruning processed raw data...")
                deleted_count = await self.prune_raw_data(session, start_time, end_time)
                
                self.logger.info(f"Aggregation cycle complete: {saved_count} aggregates saved, {deleted_count} raw records pruned")
                return True
                
        except Exception as e:
            self.logger.error(f"Aggregation cycle failed: {e}")
            return False
    
    async def run_continuous(self, interval_hours: int = 1):
        """
        Run the aggregator continuously with the specified interval.
        
        Args:
            interval_hours: Hours between aggregation cycles
        """
        self.logger.info(f"Starting telemetry aggregator (interval: {interval_hours} hour(s))")
        
        while True:
            try:
                success = await self.run_aggregation_cycle()
                if not success:
                    self.logger.error("Aggregation cycle failed, will retry on next interval")
                
                # Wait for the next cycle
                interval_seconds = interval_hours * 3600
                self.logger.info(f"Waiting {interval_hours} hour(s) until next aggregation cycle...")
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Aggregator stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in aggregator loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)


async def main():
    """Main entry point for the aggregator worker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Telemetry Aggregator Worker")
    parser.add_argument("--once", action="store_true", help="Run one aggregation cycle and exit")
    parser.add_argument("--interval", type=int, default=1, help="Hours between aggregation cycles (default: 1)")
    
    args = parser.parse_args()
    
    aggregator = TelemetryAggregator()
    
    if args.once:
        logger.info("Running single aggregation cycle...")
        success = await aggregator.run_aggregation_cycle()
        if success:
            logger.info("Single aggregation cycle completed successfully")
        else:
            logger.error("Single aggregation cycle failed")
            sys.exit(1)
    else:
        await aggregator.run_continuous(args.interval)


if __name__ == "__main__":
    asyncio.run(main()) 