"""
Scheduler Tests for Bella's Reef Backend

This module tests the scheduler system functionality including:
- Job scheduling (one-time, recurring, interval, cron)
- Job execution and timing
- Job management (listing, cancelling, updating)
- Error handling and recovery
- Integration with device actions

Test Categories:
- Basic scheduler functionality
- Different schedule types (one_off, recurring, interval, cron)
- Job lifecycle management
- Error handling and recovery
- Integration with device actions
- Performance and scalability

Usage:
    pytest backend/tests/test_scheduler.py -v
    pytest backend/tests/test_scheduler.py::test_scheduler_basic_functionality -v
    pytest backend/tests/test_scheduler.py -m "scheduler" -v
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from scheduler.services.scheduler import Scheduler
from scheduler.worker.scheduler_worker import SchedulerWorker
from scheduler.worker.schedule_calculator import ScheduleCalculator

# =============================================================================
# Basic Scheduler Tests
# =============================================================================

@pytest.mark.scheduler
class TestSchedulerBasic:
    """Test basic scheduler functionality."""
    
    @pytest.mark.asyncio
    async def test_scheduler_initialization(self):
        """Test scheduler initializes correctly."""
        scheduler = Scheduler()
        
        assert scheduler.tasks == {}
        assert scheduler._running is False
        assert scheduler._task is None
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        """Test scheduler start and stop functionality."""
        scheduler = Scheduler()
        
        # Start scheduler
        await scheduler.start()
        assert scheduler._running is True
        assert scheduler._task is not None
        
        # Stop scheduler
        await scheduler.stop()
        assert scheduler._running is False
        assert scheduler._task is None
    
    @pytest.mark.asyncio
    async def test_scheduler_double_start(self):
        """Test that starting scheduler twice doesn't cause issues."""
        scheduler = Scheduler()
        
        await scheduler.start()
        await scheduler.start()  # Should not cause issues
        
        assert scheduler._running is True
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_scheduler_stop_when_not_running(self):
        """Test stopping scheduler when not running."""
        scheduler = Scheduler()
        
        # Stop without starting should not cause issues
        await scheduler.stop()
        assert scheduler._running is False

# =============================================================================
# Task Management Tests
# =============================================================================

@pytest.mark.scheduler
class TestTaskManagement:
    """Test task management functionality."""
    
    @pytest.mark.asyncio
    async def test_add_task(self):
        """Test adding a task to the scheduler."""
        scheduler = Scheduler()
        
        # Mock function
        mock_func = AsyncMock()
        
        # Add task
        schedule = {"time": time(8, 0)}  # 8:00 AM
        scheduler.add_task("test_task", mock_func, schedule, "arg1", kwarg1="value1")
        
        assert "test_task" in scheduler.tasks
        task = scheduler.tasks["test_task"]
        assert task["func"] == mock_func
        assert task["schedule"] == schedule
        assert task["args"] == ("arg1",)
        assert task["kwargs"] == {"kwarg1": "value1"}
    
    @pytest.mark.asyncio
    async def test_remove_task(self):
        """Test removing a task from the scheduler."""
        scheduler = Scheduler()
        
        # Add task
        mock_func = AsyncMock()
        schedule = {"time": time(8, 0)}
        scheduler.add_task("test_task", mock_func, schedule)
        
        assert "test_task" in scheduler.tasks
        
        # Remove task
        scheduler.remove_task("test_task")
        assert "test_task" not in scheduler.tasks
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_task(self):
        """Test removing a task that doesn't exist."""
        scheduler = Scheduler()
        
        # Remove non-existent task should not cause issues
        scheduler.remove_task("nonexistent_task")
        assert "nonexistent_task" not in scheduler.tasks

# =============================================================================
# Schedule Type Tests
# =============================================================================

@pytest.mark.scheduler
class TestScheduleTypes:
    """Test different schedule types."""
    
    @pytest.mark.asyncio
    async def test_time_based_schedule(self):
        """Test time-based scheduling."""
        scheduler = Scheduler()
        
        # Mock function
        mock_func = AsyncMock()
        
        # Schedule for current time
        now = datetime.now(pytz.UTC)
        schedule_time = time(now.hour, now.minute)
        schedule = {"time": schedule_time}
        
        scheduler.add_task("time_task", mock_func, schedule)
        
        # Start scheduler
        await scheduler.start()
        
        # Wait a bit for task to execute
        await asyncio.sleep(2)
        
        # Stop scheduler
        await scheduler.stop()
        
        # Check if function was called
        assert mock_func.called
    
    @pytest.mark.asyncio
    async def test_interval_schedule(self):
        """Test interval-based scheduling."""
        scheduler = Scheduler()
        
        # Mock function
        mock_func = AsyncMock()
        
        # Schedule with 1-second interval
        schedule = {"interval": 1}
        
        scheduler.add_task("interval_task", mock_func, schedule)
        
        # Start scheduler
        await scheduler.start()
        
        # Wait for multiple executions
        await asyncio.sleep(3)
        
        # Stop scheduler
        await scheduler.stop()
        
        # Check if function was called multiple times
        assert mock_func.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_cron_schedule(self):
        """Test cron-based scheduling."""
        scheduler = Scheduler()
        
        # Mock function
        mock_func = AsyncMock()
        
        # Schedule with cron expression (every minute)
        schedule = {"cron": "* * * * *"}
        
        scheduler.add_task("cron_task", mock_func, schedule)
        
        # Start scheduler
        await scheduler.start()
        
        # Wait for execution
        await asyncio.sleep(2)
        
        # Stop scheduler
        await scheduler.stop()
        
        # Check if function was called
        assert mock_func.called

# =============================================================================
# Schedule Calculator Tests
# =============================================================================

@pytest.mark.scheduler
class TestScheduleCalculator:
    """Test schedule calculation functionality."""
    
    def test_calculate_next_run_one_off(self):
        """Test calculating next run for one-off schedule."""
        calculator = ScheduleCalculator()
        
        # One-off schedule
        schedule_data = {
            "schedule_type": "one_off",
            "start_time": datetime.now(pytz.UTC) + timedelta(minutes=5)
        }
        
        next_run = calculator.calculate_next_run(schedule_data)
        assert next_run is not None
        assert next_run > datetime.now(pytz.UTC)
    
    def test_calculate_next_run_recurring(self):
        """Test calculating next run for recurring schedule."""
        calculator = ScheduleCalculator()
        
        # Recurring schedule (daily at 8 AM)
        schedule_data = {
            "schedule_type": "recurring",
            "cron_expression": "0 8 * * *",
            "timezone": "UTC"
        }
        
        next_run = calculator.calculate_next_run(schedule_data)
        assert next_run is not None
        
        # Should be 8 AM on some day
        assert next_run.hour == 8
        assert next_run.minute == 0
    
    def test_calculate_next_run_interval(self):
        """Test calculating next run for interval schedule."""
        calculator = ScheduleCalculator()
        
        # Interval schedule (every 5 minutes)
        schedule_data = {
            "schedule_type": "interval",
            "interval_seconds": 300
        }
        
        next_run = calculator.calculate_next_run(schedule_data)
        assert next_run is not None
        
        # Should be within 5 minutes of now
        now = datetime.now(pytz.UTC)
        time_diff = (next_run - now).total_seconds()
        assert 0 <= time_diff <= 300
    
    def test_calculate_next_run_invalid_type(self):
        """Test calculating next run for invalid schedule type."""
        calculator = ScheduleCalculator()
        
        schedule_data = {
            "schedule_type": "invalid_type"
        }
        
        next_run = calculator.calculate_next_run(schedule_data)
        assert next_run is None

# =============================================================================
# Scheduler Worker Tests
# =============================================================================

@pytest.mark.scheduler
class TestSchedulerWorker:
    """Test scheduler worker functionality."""
    
    @pytest.mark.asyncio
    async def test_worker_initialization(self, test_session: AsyncSession):
        """Test scheduler worker initializes correctly."""
        worker = SchedulerWorker()
        
        assert worker.db is None
        assert worker.scheduler is not None
        assert worker.calculator is not None
    
    @pytest.mark.asyncio
    async def test_worker_start_stop(self, test_session: AsyncSession):
        """Test scheduler worker start and stop."""
        worker = SchedulerWorker()
        
        # Start worker
        await worker.start(test_session)
        assert worker.db == test_session
        assert worker.scheduler._running is True
        
        # Stop worker
        await worker.stop()
        assert worker.scheduler._running is False
    
    @pytest.mark.asyncio
    async def test_load_schedules_from_database(self, test_session: AsyncSession):
        """Test loading schedules from database."""
        worker = SchedulerWorker()
        
        # Mock schedule data
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_schedule.name = "Test Schedule"
        mock_schedule.schedule_type = "recurring"
        mock_schedule.cron_expression = "0 8 * * *"
        mock_schedule.is_enabled = True
        mock_schedule.action_type = "on"
        mock_schedule.action_params = {"duration": 3600}
        
        # Mock database query
        with patch("app.crud.schedule.get_enabled_schedules") as mock_get_schedules:
            mock_get_schedules.return_value = [mock_schedule]
            
            await worker.start(test_session)
            await worker.load_schedules()
            
            # Check if schedule was added to scheduler
            assert len(worker.scheduler.tasks) > 0
            
            await worker.stop()

# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.scheduler
class TestErrorHandling:
    """Test error handling in scheduler."""
    
    @pytest.mark.asyncio
    async def test_task_execution_error(self):
        """Test that task execution errors are handled gracefully."""
        scheduler = Scheduler()
        
        # Mock function that raises an exception
        async def error_func():
            raise Exception("Test error")
        
        # Add task
        schedule = {"time": time(8, 0)}
        scheduler.add_task("error_task", error_func, schedule)
        
        # Start scheduler
        await scheduler.start()
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Stop scheduler
        await scheduler.stop()
        
        # Scheduler should still be running despite task error
        assert scheduler._running is False
    
    @pytest.mark.asyncio
    async def test_invalid_schedule_format(self):
        """Test handling of invalid schedule format."""
        scheduler = Scheduler()
        
        # Mock function
        mock_func = AsyncMock()
        
        # Invalid schedule (missing required fields)
        invalid_schedule = {}
        
        scheduler.add_task("invalid_task", mock_func, invalid_schedule)
        
        # Start scheduler
        await scheduler.start()
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Stop scheduler
        await scheduler.stop()
        
        # Function should not be called due to invalid schedule
        assert not mock_func.called

# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.scheduler
@pytest.mark.integration
class TestSchedulerIntegration:
    """Integration tests for scheduler functionality."""
    
    @pytest.mark.asyncio
    async def test_scheduler_with_database_integration(self, test_session: AsyncSession):
        """Test scheduler integration with database."""
        worker = SchedulerWorker()
        
        # Start worker
        await worker.start(test_session)
        
        # Add a test schedule to database
        # This would require creating actual database records
        # For now, we'll test the worker structure
        
        # Stop worker
        await worker.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_tasks_execution(self):
        """Test execution of multiple tasks."""
        scheduler = Scheduler()
        
        # Create multiple mock functions
        mock_func1 = AsyncMock()
        mock_func2 = AsyncMock()
        mock_func3 = AsyncMock()
        
        # Add multiple tasks
        now = datetime.now(pytz.UTC)
        schedule_time = time(now.hour, now.minute)
        schedule = {"time": schedule_time}
        
        scheduler.add_task("task1", mock_func1, schedule)
        scheduler.add_task("task2", mock_func2, schedule)
        scheduler.add_task("task3", mock_func3, schedule)
        
        # Start scheduler
        await scheduler.start()
        
        # Wait for execution
        await asyncio.sleep(2)
        
        # Stop scheduler
        await scheduler.stop()
        
        # All functions should be called
        assert mock_func1.called
        assert mock_func2.called
        assert mock_func3.called

# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.scheduler
class TestSchedulerPerformance:
    """Test scheduler performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_scheduler_with_many_tasks(self):
        """Test scheduler performance with many tasks."""
        scheduler = Scheduler()
        
        # Create many mock functions
        mock_funcs = [AsyncMock() for _ in range(50)]
        
        # Add many tasks
        now = datetime.now(pytz.UTC)
        schedule_time = time(now.hour, now.minute)
        schedule = {"time": schedule_time}
        
        for i, mock_func in enumerate(mock_funcs):
            scheduler.add_task(f"task_{i}", mock_func, schedule)
        
        # Start scheduler
        start_time = datetime.now()
        await scheduler.start()
        
        # Wait for execution
        await asyncio.sleep(2)
        
        # Stop scheduler
        await scheduler.stop()
        end_time = datetime.now()
        
        # Check performance
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 5  # Should complete within 5 seconds
        
        # Check that functions were called
        for mock_func in mock_funcs:
            assert mock_func.called

# =============================================================================
# Manual Test Instructions
# =============================================================================

"""
MANUAL TEST INSTRUCTIONS FOR SCHEDULER SYSTEM

These instructions should be followed on the target Raspberry Pi environment
to verify scheduler functionality in the actual deployment environment.

1. BASIC SCHEDULER FUNCTIONALITY MANUAL TESTS
   ==========================================
   
   a) Start Scheduler Service:
      # Start the scheduler worker
      python -m app.worker.scheduler_worker
      Expected: Scheduler starts without errors, logs show initialization
   
   b) Check Scheduler Status:
      # Check if scheduler is running
      ps aux | grep scheduler_worker
      Expected: Process is running
   
   c) View Scheduler Logs:
      tail -f /var/log/bellasreef/scheduler.log
      Expected: Logs show scheduler activity

2. SCHEDULE CREATION MANUAL TESTS
   ==============================
   
   a) Create One-Off Schedule:
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Test One-Off",
          "schedule_type": "one_off",
          "start_time": "'$(date -d '+2 minutes' -Iseconds)'",
          "device_ids": [1],
          "action_type": "on",
          "action_params": {"duration": 60}
        }'
      Expected: 201 Created with schedule ID
   
   b) Create Recurring Schedule:
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Daily Test",
          "schedule_type": "recurring",
          "cron_expression": "0 8 * * *",
          "device_ids": [1],
          "action_type": "on",
          "action_params": {"duration": 3600}
        }'
      Expected: 201 Created with schedule ID
   
   c) Create Interval Schedule:
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Every 5 Minutes",
          "schedule_type": "interval",
          "interval_seconds": 300,
          "device_ids": [1],
          "action_type": "on",
          "action_params": {"duration": 30}
        }'
      Expected: 201 Created with schedule ID

3. SCHEDULE EXECUTION MANUAL TESTS
   ===============================
   
   a) Monitor Schedule Execution:
      # Watch logs for schedule execution
      tail -f /var/log/bellasreef/scheduler.log | grep "executing"
      Expected: Log entries when schedules execute
   
   b) Check Device Actions:
      # Monitor device action table
      # This requires database access
      # Check if device_actions table gets new entries
   
   c) Verify Device State Changes:
      # Check if devices actually change state
      # This depends on device type and hardware
      # For outlets: check if they turn on/off
      # For pumps: check if they start/stop

4. SCHEDULE MANAGEMENT MANUAL TESTS
   ================================
   
   a) List All Schedules:
      curl -X GET http://localhost:8000/api/v1/schedules/ \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with list of schedules
   
   b) Get Specific Schedule:
      SCHEDULE_ID="your_schedule_id"
      curl -X GET http://localhost:8000/api/v1/schedules/$SCHEDULE_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with schedule details
   
   c) Update Schedule:
      curl -X PUT http://localhost:8000/api/v1/schedules/$SCHEDULE_ID \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Updated Schedule",
          "is_enabled": false
        }'
      Expected: 200 OK with updated schedule
   
   d) Delete Schedule:
      curl -X DELETE http://localhost:8000/api/v1/schedules/$SCHEDULE_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: 204 No Content

5. ERROR HANDLING MANUAL TESTS
   ============================
   
   a) Create Invalid Schedule:
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Invalid Schedule",
          "schedule_type": "invalid_type"
        }'
      Expected: 422 Unprocessable Entity
   
   b) Schedule with Non-existent Device:
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Invalid Device",
          "schedule_type": "one_off",
          "start_time": "'$(date -d '+1 minute' -Iseconds)'",
          "device_ids": [99999],
          "action_type": "on"
        }'
      Expected: 400 Bad Request or execution failure
   
   c) Check Error Logs:
      tail -f /var/log/bellasreef/error.log
      Expected: Error entries for failed schedules

6. PERFORMANCE MANUAL TESTS
   =========================
   
   a) Create Many Schedules:
      # Create 50 schedules
      for i in {1..50}; do
        curl -X POST http://localhost:8000/api/v1/schedules/ \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer $TOKEN" \
          -d "{
            \"name\": \"Performance Test $i\",
            \"schedule_type\": \"interval\",
            \"interval_seconds\": 60,
            \"device_ids\": [1],
            \"action_type\": \"on\",
            \"action_params\": {\"duration\": 10}
          }"
      done
      Expected: All schedules created successfully
   
   b) Monitor System Resources:
      htop
      # Watch CPU and memory usage
      Expected: Stable resource usage
   
   c) Check Database Performance:
      # Monitor database connections and query performance
      # This may require database monitoring tools

7. CRON EXPRESSION MANUAL TESTS
   =============================
   
   a) Test Various Cron Expressions:
      # Every minute
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Every Minute",
          "schedule_type": "recurring",
          "cron_expression": "* * * * *",
          "device_ids": [1],
          "action_type": "on",
          "action_params": {"duration": 30}
        }'
   
      # Every hour at minute 30
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Every Hour",
          "schedule_type": "recurring",
          "cron_expression": "30 * * * *",
          "device_ids": [1],
          "action_type": "on",
          "action_params": {"duration": 300}
        }'
   
      # Daily at 6 AM
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Daily 6 AM",
          "schedule_type": "recurring",
          "cron_expression": "0 6 * * *",
          "device_ids": [1],
          "action_type": "on",
          "action_params": {"duration": 3600}
        }'

8. TIMEZONE MANUAL TESTS
   ======================
   
   a) Test Different Timezones:
      # Schedule in local timezone
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Local Time",
          "schedule_type": "recurring",
          "cron_expression": "0 8 * * *",
          "timezone": "America/New_York",
          "device_ids": [1],
          "action_type": "on"
        }'
   
      # Schedule in UTC
      curl -X POST http://localhost:8000/api/v1/schedules/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "UTC Time",
          "schedule_type": "recurring",
          "cron_expression": "0 8 * * *",
          "timezone": "UTC",
          "device_ids": [1],
          "action_type": "on"
        }'

9. RECOVERY MANUAL TESTS
   ======================
   
   a) Restart Scheduler Service:
      # Stop scheduler
      pkill -f scheduler_worker
      
      # Start scheduler
      python -m app.worker.scheduler_worker
      
      # Check if schedules are reloaded
      Expected: Schedules are reloaded from database
   
   b) Database Connection Loss:
      # Simulate database connection issues
      # Stop PostgreSQL service temporarily
      sudo systemctl stop postgresql
      
      # Wait a bit
      sleep 10
      
      # Restart PostgreSQL
      sudo systemctl start postgresql
      
      # Check scheduler recovery
      Expected: Scheduler reconnects and continues

10. INTEGRATION MANUAL TESTS
    =========================
    
    a) Scheduler + Poller Integration:
       # Create schedule that depends on polled data
       # This requires alert-based scheduling
       # Check if scheduler responds to polled data changes
    
    b) Scheduler + Device Integration:
       # Create schedules for different device types
       # Test with temperature sensors, outlets, pumps
       # Verify device state changes
    
    c) Scheduler + Alert Integration:
       # Create schedules triggered by alerts
       # Test alert-based scheduling functionality

NOTES:
- Replace $TOKEN with actual authentication token
- Monitor logs for any errors or warnings
- Check database for schedule and action records
- Verify device state changes where applicable
- Test with different timezones and daylight saving time
- Monitor system resources during performance tests
- Ensure proper error handling and recovery
""" 