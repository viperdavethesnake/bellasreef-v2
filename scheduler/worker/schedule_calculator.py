"""
Schedule calculation logic for Bella's Reef scheduler system.

This module provides the core logic for calculating next run times for different
schedule types, handling timezone conversions, and managing schedule execution.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.models import Schedule, DeviceAction, Device
from shared.crud.schedule import schedule as schedule_crud, device_action as device_action_crud
from shared.schemas.schedule import ScheduleCreate, DeviceActionCreate, ActionTypeEnum

logger = logging.getLogger(__name__)

class ScheduleCalculator:
    """
    Calculates next run times for different schedule types.
    
    This class handles:
    - Timezone conversions (UTC <-> local time)
    - Next run time calculations for all schedule types
    - Schedule validation and error handling
    - Bulk schedule processing
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def calculate_next_run(self, schedule: Schedule, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calculate the next run time for a schedule.
        
        Args:
            schedule: The schedule to calculate next run for
            current_time: Current time (defaults to UTC now)
            
        Returns:
            Next run time in UTC, or None if schedule is invalid/expired
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        try:
            if schedule.schedule_type == "one_off":
                return self._calculate_one_off_next_run(schedule, current_time)
            elif schedule.schedule_type == "interval":
                return self._calculate_interval_next_run(schedule, current_time)
            elif schedule.schedule_type == "cron":
                return self._calculate_cron_next_run(schedule, current_time)
            elif schedule.schedule_type == "recurring":
                return self._calculate_recurring_next_run(schedule, current_time)
            elif schedule.schedule_type == "static":
                return self._calculate_static_next_run(schedule, current_time)
            else:
                logger.error(f"Unknown schedule type: {schedule.schedule_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating next run for schedule {schedule.id}: {e}")
            return None
    
    def _calculate_one_off_next_run(self, schedule: Schedule, current_time: datetime) -> Optional[datetime]:
        """Calculate next run for one-off schedules."""
        if not schedule.start_time:
            logger.error(f"One-off schedule {schedule.id} missing start_time")
            return None
        
        # Convert start_time to UTC if it's not already
        start_time_utc = schedule.start_time
        if start_time_utc.tzinfo is None:
            # Assume it's in the schedule's timezone
            start_time_utc = self._local_to_utc(start_time_utc, schedule.timezone)
        
        # If start time is in the past, schedule is expired
        if start_time_utc <= current_time:
            return None
        
        return start_time_utc
    
    def _calculate_interval_next_run(self, schedule: Schedule, current_time: datetime) -> Optional[datetime]:
        """Calculate next run for interval schedules."""
        if not schedule.interval_seconds:
            logger.error(f"Interval schedule {schedule.id} missing interval_seconds")
            return None
        
        # Use last_run if available, otherwise use start_time or current_time
        base_time = schedule.last_run or schedule.start_time or current_time
        
        # Convert to UTC if needed
        if base_time.tzinfo is None:
            base_time = self._local_to_utc(base_time, schedule.timezone)
        
        # Calculate next run
        next_run = base_time + timedelta(seconds=schedule.interval_seconds)
        
        # Check if we've passed the end time
        if schedule.end_time and next_run > schedule.end_time:
            return None
        
        return next_run
    
    def _calculate_cron_next_run(self, schedule: Schedule, current_time: datetime) -> Optional[datetime]:
        """Calculate next run for cron schedules."""
        if not schedule.cron_expression:
            logger.error(f"Cron schedule {schedule.id} missing cron_expression")
            return None
        
        try:
            # Simple cron parsing for common patterns
            # In production, use a proper cron library like croniter
            next_run = self._parse_cron_expression(schedule.cron_expression, current_time, schedule.timezone)
            return next_run
        except Exception as e:
            logger.error(f"Error parsing cron expression for schedule {schedule.id}: {e}")
            return None
    
    def _calculate_recurring_next_run(self, schedule: Schedule, current_time: datetime) -> Optional[datetime]:
        """Calculate next run for recurring schedules."""
        if not schedule.start_time:
            logger.error(f"Recurring schedule {schedule.id} missing start_time")
            return None
        
        # Parse recurring pattern from action_params
        pattern = schedule.action_params.get("recurring_pattern", {}) if schedule.action_params else {}
        frequency = pattern.get("frequency", "daily")  # daily, weekly, monthly
        
        base_time = schedule.last_run or schedule.start_time
        
        # Convert to UTC if needed
        if base_time.tzinfo is None:
            base_time = self._local_to_utc(base_time, schedule.timezone)
        
        # Calculate next occurrence based on frequency
        if frequency == "daily":
            next_run = base_time + timedelta(days=1)
        elif frequency == "weekly":
            next_run = base_time + timedelta(weeks=1)
        elif frequency == "monthly":
            # Simple monthly calculation (30 days)
            next_run = base_time + timedelta(days=30)
        else:
            logger.error(f"Unknown recurring frequency: {frequency}")
            return None
        
        # Check if we've passed the end time
        if schedule.end_time and next_run > schedule.end_time:
            return None
        
        return next_run
    
    def _calculate_static_next_run(self, schedule: Schedule, current_time: datetime) -> Optional[datetime]:
        """Calculate next run for static schedules (prepopulated)."""
        # Static schedules typically run on a daily cycle
        # For now, assume they run daily at the same time
        if not schedule.start_time:
            logger.error(f"Static schedule {schedule.id} missing start_time")
            return None
        
        # Convert start_time to today's date
        start_time_utc = schedule.start_time
        if start_time_utc.tzinfo is None:
            start_time_utc = self._local_to_utc(start_time_utc, schedule.timezone)
        
        # Calculate today's run time
        today = current_time.date()
        today_run = datetime.combine(today, start_time_utc.time(), tzinfo=timezone.utc)
        
        # If today's run time has passed, schedule for tomorrow
        if today_run <= current_time:
            tomorrow = today + timedelta(days=1)
            today_run = datetime.combine(tomorrow, start_time_utc.time(), tzinfo=timezone.utc)
        
        return today_run
    
    def _parse_cron_expression(self, cron_expr: str, current_time: datetime, timezone_str: str) -> datetime:
        """
        Parse a cron expression and calculate next run time.
        
        This is a simplified implementation. In production, use a proper cron library.
        """
        # Simple cron parsing for common patterns
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")
        
        minute, hour, day, month, weekday = parts
        
        # For now, implement basic daily scheduling
        # In production, use croniter or similar library
        if minute == "*" and hour == "*" and day == "*" and month == "*" and weekday == "*":
            # Every minute
            return current_time + timedelta(minutes=1)
        elif minute != "*" and hour == "*" and day == "*" and month == "*" and weekday == "*":
            # Every hour at specific minute
            next_run = current_time.replace(minute=int(minute), second=0, microsecond=0)
            if next_run <= current_time:
                next_run += timedelta(hours=1)
            return next_run
        elif minute != "*" and hour != "*" and day == "*" and month == "*" and weekday == "*":
            # Daily at specific time
            next_run = current_time.replace(
                hour=int(hour), 
                minute=int(minute), 
                second=0, 
                microsecond=0
            )
            if next_run <= current_time:
                next_run += timedelta(days=1)
            return next_run
        else:
            # For complex patterns, return current time + 1 hour as fallback
            logger.warning(f"Complex cron expression not fully supported: {cron_expr}")
            return current_time + timedelta(hours=1)
    
    def _local_to_utc(self, local_time: datetime, timezone_str: str) -> datetime:
        """Convert local time to UTC."""
        # Simplified timezone conversion
        # In production, use pytz or zoneinfo for proper timezone handling
        if timezone_str == "UTC":
            return local_time.replace(tzinfo=timezone.utc)
        else:
            # Assume local time is already in UTC for now
            return local_time.replace(tzinfo=timezone.utc)
    
    def _utc_to_local(self, utc_time: datetime, timezone_str: str) -> datetime:
        """Convert UTC time to local time."""
        # Simplified timezone conversion
        # In production, use pytz or zoneinfo for proper timezone handling
        if timezone_str == "UTC":
            return utc_time
        else:
            # Return UTC time for now
            return utc_time
    
    async def process_due_schedules(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Process all schedules that are due to run.
        
        Args:
            current_time: Current time (defaults to UTC now)
            
        Returns:
            Dict containing processing statistics
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        logger.info(f"Processing due schedules at {current_time}")
        
        # Get all due schedules
        due_schedules = await schedule_crud.get_due_schedules(self.db, current_time)
        logger.info(f"Found {len(due_schedules)} schedules due to run")
        
        stats = {
            "total_due": len(due_schedules),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": 0
        }
        
        for schedule in due_schedules:
            try:
                result = await self._process_single_schedule(schedule, current_time)
                stats["processed"] += 1
                
                if result["success"]:
                    stats["successful"] += 1
                    logger.info(f"Successfully processed schedule {schedule.id}: {result['message']}")
                else:
                    stats["failed"] += 1
                    logger.warning(f"Failed to process schedule {schedule.id}: {result['message']}")
                    
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error processing schedule {schedule.id}: {e}")
        
        logger.info(f"Schedule processing complete: {stats}")
        return stats
    
    async def _process_single_schedule(self, schedule: Schedule, current_time: datetime) -> Dict[str, Any]:
        """
        Process a single schedule and create device actions.
        
        Args:
            schedule: The schedule to process
            current_time: Current time
            
        Returns:
            Dict containing processing result
        """
        try:
            # Validate schedule
            validation = self.validate_schedule(schedule)
            if not validation["valid"]:
                return {
                    "success": False,
                    "message": f"Schedule validation failed: {validation['errors']}"
                }
            
            # Create device actions for each device in the schedule
            actions_created = []
            for device_id in schedule.device_ids:
                try:
                    # Verify device exists and is active
                    device = await self._get_device(device_id)
                    if not device:
                        logger.warning(f"Device {device_id} not found for schedule {schedule.id}")
                        continue
                    
                    if not device.is_active:
                        logger.warning(f"Device {device_id} is inactive for schedule {schedule.id}")
                        continue
                    
                    # Create device action
                    action_data = DeviceActionCreate(
                        schedule_id=schedule.id,
                        device_id=device_id,
                        action_type=schedule.action_type,
                        parameters=schedule.action_params,
                        scheduled_time=current_time
                    )
                    
                    action = await device_action_crud.create(self.db, action_data)
                    actions_created.append(action)
                    
                except Exception as e:
                    logger.error(f"Error creating action for device {device_id}: {e}")
            
            if not actions_created:
                return {
                    "success": False,
                    "message": "No device actions were created"
                }
            
            # Update schedule with next run time
            next_run = self.calculate_next_run(schedule, current_time)
            if next_run:
                await schedule_crud.update_next_run(self.db, schedule.id, next_run)
            else:
                # Schedule is expired, disable it
                await schedule_crud.update(self.db, schedule, {"is_enabled": False})
                logger.info(f"Schedule {schedule.id} expired and disabled")
            
            # Update last run time
            await schedule_crud.update_last_run(self.db, schedule.id, current_time, "success")
            
            return {
                "success": True,
                "message": f"Created {len(actions_created)} device actions",
                "actions_created": len(actions_created)
            }
            
        except Exception as e:
            # Update schedule with error status
            await schedule_crud.update_last_run(self.db, schedule.id, current_time, "failed")
            raise e
    
    async def _get_device(self, device_id: int) -> Optional[Device]:
        """Get a device by ID."""
        from sqlalchemy import select
        result = await self.db.execute(select(Device).filter(Device.id == device_id))
        return result.scalar_one_or_none()
    
    def validate_schedule(self, schedule: Schedule) -> Dict[str, Any]:
        """
        Validate a schedule configuration.
        
        Args:
            schedule: The schedule to validate
            
        Returns:
            Dict containing validation result
        """
        errors = []
        
        # Check required fields based on schedule type
        if schedule.schedule_type == "one_off":
            if not schedule.start_time:
                errors.append("One-off schedule requires start_time")
        elif schedule.schedule_type == "interval":
            if not schedule.interval_seconds:
                errors.append("Interval schedule requires interval_seconds")
        elif schedule.schedule_type == "cron":
            if not schedule.cron_expression:
                errors.append("Cron schedule requires cron_expression")
        elif schedule.schedule_type == "recurring":
            if not schedule.start_time:
                errors.append("Recurring schedule requires start_time")
        elif schedule.schedule_type == "static":
            if not schedule.start_time:
                errors.append("Static schedule requires start_time")
        
        # Check device_ids
        if not schedule.device_ids:
            errors.append("Schedule must have at least one device")
        
        # Check action_type
        if not schedule.action_type:
            errors.append("Schedule must have an action_type")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        } 