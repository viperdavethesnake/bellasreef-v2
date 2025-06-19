"""
Schedule calculation logic for Bella's Reef scheduler system.

This module provides the core logic for calculating next run times for different
schedule types, handling timezone conversions, and managing schedule execution.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.db.models import Schedule, DeviceAction, Device
from app.crud.schedule import schedule as schedule_crud, device_action as device_action_crud
from app.schemas.schedule import ScheduleCreate, DeviceActionCreate, ActionTypeEnum

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
    
    def __init__(self, db: Session):
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
            next_run = current_time.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            if next_run <= current_time:
                next_run += timedelta(days=1)
            return next_run
        else:
            # For complex cron expressions, return current time + 1 hour as fallback
            logger.warning(f"Complex cron expression not fully supported: {cron_expr}")
            return current_time + timedelta(hours=1)
    
    def _local_to_utc(self, local_time: datetime, timezone_str: str) -> datetime:
        """
        Convert local time to UTC.
        
        This is a simplified implementation. In production, use pytz or zoneinfo.
        """
        # For now, assume the time is already in UTC
        # In production, implement proper timezone conversion
        if local_time.tzinfo is None:
            # Assume UTC for now
            return local_time.replace(tzinfo=timezone.utc)
        return local_time
    
    def _utc_to_local(self, utc_time: datetime, timezone_str: str) -> datetime:
        """
        Convert UTC time to local time.
        
        This is a simplified implementation. In production, use pytz or zoneinfo.
        """
        # For now, return UTC time as-is
        # In production, implement proper timezone conversion
        return utc_time
    
    def process_due_schedules(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Process all schedules that are due to run.
        
        Args:
            current_time: Current time (defaults to UTC now)
            
        Returns:
            Dictionary with processing statistics
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        logger.info(f"Processing due schedules at {current_time}")
        
        stats = {
            "total_schedules": 0,
            "processed": 0,
            "actions_created": 0,
            "errors": 0,
            "skipped": 0
        }
        
        # Get all due schedules
        due_schedules = schedule_crud.get_due_schedules(self.db, current_time)
        stats["total_schedules"] = len(due_schedules)
        
        for schedule in due_schedules:
            try:
                result = self._process_single_schedule(schedule, current_time)
                stats["processed"] += 1
                stats["actions_created"] += result.get("actions_created", 0)
                
                if result.get("skipped"):
                    stats["skipped"] += 1
                    
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error processing schedule {schedule.id}: {e}")
        
        logger.info(f"Schedule processing complete: {stats}")
        return stats
    
    def _process_single_schedule(self, schedule: Schedule, current_time: datetime) -> Dict[str, Any]:
        """
        Process a single schedule that is due to run.
        
        Args:
            schedule: The schedule to process
            current_time: Current time
            
        Returns:
            Dictionary with processing result
        """
        # Validate schedule
        if not schedule.is_enabled:
            return {"skipped": True, "reason": "Schedule disabled"}
        
        if not schedule.device_ids:
            return {"skipped": True, "reason": "No devices specified"}
        
        # Create device actions
        actions_created = 0
        for device_id in schedule.device_ids:
            try:
                action_data = DeviceActionCreate(
                    schedule_id=schedule.id,
                    device_id=device_id,
                    action_type=schedule.action_type,
                    parameters=schedule.action_params,
                    scheduled_time=current_time
                )
                
                device_action_crud.create(self.db, action_data)
                actions_created += 1
                
            except Exception as e:
                logger.error(f"Error creating action for device {device_id}: {e}")
        
        # Update schedule last run
        schedule_crud.update_last_run(self.db, schedule.id, current_time, "success")
        
        # Calculate next run time
        next_run = self.calculate_next_run(schedule, current_time)
        if next_run:
            schedule_crud.update_next_run(self.db, schedule.id, next_run)
        else:
            # Schedule is expired or invalid, disable it
            schedule_crud.update(self.db, schedule, {"is_enabled": False})
            logger.info(f"Schedule {schedule.id} expired, disabled")
        
        return {
            "actions_created": actions_created,
            "next_run": next_run
        }
    
    def validate_schedule(self, schedule: Schedule) -> Dict[str, Any]:
        """
        Validate a schedule configuration.
        
        Args:
            schedule: The schedule to validate
            
        Returns:
            Dictionary with validation result
        """
        errors = []
        warnings = []
        
        # Check required fields based on schedule type
        if schedule.schedule_type == "one_off" and not schedule.start_time:
            errors.append("One-off schedules require start_time")
        
        if schedule.schedule_type == "interval" and not schedule.interval_seconds:
            errors.append("Interval schedules require interval_seconds")
        
        if schedule.schedule_type == "cron" and not schedule.cron_expression:
            errors.append("Cron schedules require cron_expression")
        
        if schedule.schedule_type == "recurring" and not schedule.start_time:
            errors.append("Recurring schedules require start_time")
        
        # Check device IDs
        if not schedule.device_ids:
            errors.append("At least one device_id is required")
        else:
            # Validate that devices exist
            for device_id in schedule.device_ids:
                device = self.db.query(Device).filter(Device.id == device_id).first()
                if not device:
                    errors.append(f"Device {device_id} does not exist")
                elif not device.is_active:
                    warnings.append(f"Device {device_id} is not active")
        
        # Check timezone
        if schedule.timezone not in ["UTC", "US/Pacific", "US/Mountain", "US/Central", "US/Eastern"]:
            warnings.append(f"Timezone {schedule.timezone} may not be supported")
        
        # Check end time
        if schedule.end_time and schedule.start_time:
            if schedule.end_time <= schedule.start_time:
                errors.append("End time must be after start time")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        } 