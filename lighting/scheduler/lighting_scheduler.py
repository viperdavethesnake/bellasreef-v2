"""
Lighting Behavior Scheduler.

This module provides a scheduler that runs the lighting behavior runner
periodically to execute lighting behaviors and write to hardware through the HAL layer.
"""
import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time

from shared.utils.logger import get_logger
from lighting.runner.base_runner import LightingBehaviorRunner
from lighting.services.behavior_manager import LightingBehaviorManager

logger = get_logger(__name__)


class LightingScheduler:
    """
    Scheduler for running lighting behaviors periodically.
    
    This scheduler:
    - Runs the lighting behavior runner at regular intervals
    - Manages the runner lifecycle
    - Provides status monitoring and control
    - Handles graceful shutdown
    - Logs all operations through the behavior log system
    """
    
    def __init__(
        self, 
        interval_seconds: int = 30,
        behavior_manager: Optional[LightingBehaviorManager] = None
    ):
        """
        Initialize the lighting scheduler.
        
        Args:
            interval_seconds: Interval between runner iterations in seconds
            behavior_manager: Behavior manager instance (optional)
        """
        self.interval_seconds = interval_seconds
        self.behavior_manager = behavior_manager or LightingBehaviorManager()
        
        # Create runner with real HAL (no mocks)
        self.runner = LightingBehaviorRunner(self.behavior_manager)
        
        # Scheduler state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_iteration: Optional[datetime] = None
        self._iteration_count = 0
        self._error_count = 0
        self._start_time: Optional[datetime] = None
        
        # Statistics
        self._total_channels_processed = 0
        self._total_hardware_writes = 0
        self._total_hardware_errors = 0
        
        logger.info(f"Lighting scheduler initialized with {interval_seconds}s interval")
        
    def start(self) -> None:
        """
        Start the lighting scheduler.
        
        This method starts the background task that runs the behavior runner
        at the specified interval.
        """
        if self._running:
            logger.warning("Lighting scheduler is already running")
            return
            
        self._running = True
        self._start_time = datetime.utcnow()
        self._task = asyncio.create_task(self._scheduler_loop())
        
        logger.info(f"Lighting scheduler started with {self.interval_seconds}s interval")
        self._log_scheduler_status("scheduler_started")
        
    def stop(self) -> None:
        """
        Stop the lighting scheduler.
        
        This method gracefully stops the scheduler and waits for the current
        iteration to complete.
        """
        if not self._running:
            logger.warning("Lighting scheduler is not running")
            return
            
        logger.info("Stopping lighting scheduler...")
        self._running = False
        
        if self._task:
            self._task.cancel()
            
        self._log_scheduler_status("scheduler_stopped")
        logger.info("Lighting scheduler stopped")
        
    async def wait_for_stop(self) -> None:
        """
        Wait for the scheduler to stop.
        
        This method waits for the scheduler task to complete after calling stop().
        """
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
    def is_running(self) -> bool:
        """
        Check if the scheduler is running.
        
        Returns:
            True if scheduler is running, False otherwise
        """
        return self._running
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status information.
        
        Returns:
            Dictionary containing scheduler status
        """
        return {
            "running": self._running,
            "interval_seconds": self.interval_seconds,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "last_iteration": self._last_iteration.isoformat() if self._last_iteration else None,
            "iteration_count": self._iteration_count,
            "error_count": self._error_count,
            "total_channels_processed": self._total_channels_processed,
            "total_hardware_writes": self._total_hardware_writes,
            "total_hardware_errors": self._total_hardware_errors,
            "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds() if self._start_time else 0,
            "registered_channels": len(self.runner.get_registered_channels()),
            "hardware_status": self.runner.get_hardware_status(),
            "queue_status": self.runner.get_queue_status()
        }
        
    def get_runner(self) -> LightingBehaviorRunner:
        """
        Get the lighting behavior runner instance.
        
        Returns:
            LightingBehaviorRunner instance
        """
        return self.runner
        
    async def _scheduler_loop(self) -> None:
        """
        Main scheduler loop.
        
        This method runs continuously while the scheduler is running,
        executing the behavior runner at regular intervals.
        """
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                # Run iteration
                await self._run_iteration()
                
                # Wait for next interval
                await asyncio.sleep(self.interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                self._error_count += 1
                logger.error(f"Error in scheduler loop: {e}")
                self._log_scheduler_status("scheduler_error", error=str(e))
                
                # Wait a bit before retrying
                await asyncio.sleep(5)
                
        logger.info("Scheduler loop ended")
        
    async def _run_iteration(self) -> None:
        """
        Run a single iteration of the behavior runner.
        
        This method executes the runner and updates statistics.
        """
        try:
            start_time = datetime.utcnow()
            
            # Run the behavior runner
            intensities = self.runner.run_iteration()
            
            # Update statistics
            self._iteration_count += 1
            self._last_iteration = start_time
            self._total_channels_processed += len(intensities)
            
            # Log successful iteration
            self._log_scheduler_status(
                "iteration_completed",
                channels_processed=len(intensities),
                iteration_count=self._iteration_count
            )
            
            logger.debug(f"Iteration {self._iteration_count} completed: {len(intensities)} channels processed")
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in iteration {self._iteration_count}: {e}")
            self._log_scheduler_status("iteration_error", error=str(e))
            raise
            
    def _log_scheduler_status(
        self, 
        status: str, 
        **kwargs
    ) -> None:
        """
        Log scheduler status through the behavior log system.
        
        Args:
            status: Status message
            **kwargs: Additional context data
        """
        try:
            # Create log entry
            log_data = {
                "status": status,
                "timestamp": datetime.utcnow(),
                "scheduler_interval": self.interval_seconds,
                "iteration_count": self._iteration_count,
                "error_count": self._error_count,
                **kwargs
            }
            
            # Log through behavior manager
            # TODO: Implement actual logging through behavior manager
            # For now, just log to console
            logger.info(f"SCHEDULER_LOG: {status} - {kwargs}")
            
        except Exception as e:
            logger.error(f"Failed to log scheduler status {status}: {e}")


class LightingSchedulerService:
    """
    Service wrapper for the lighting scheduler.
    
    This class provides a service interface for managing the lighting scheduler,
    including startup, shutdown, and status monitoring.
    """
    
    def __init__(self, interval_seconds: int = 30):
        """
        Initialize the lighting scheduler service.
        
        Args:
            interval_seconds: Interval between runner iterations in seconds
        """
        self.interval_seconds = interval_seconds
        self.scheduler: Optional[LightingScheduler] = None
        
    async def start_service(self) -> None:
        """
        Start the lighting scheduler service.
        """
        if self.scheduler and self.scheduler.is_running():
            logger.warning("Lighting scheduler service is already running")
            return
            
        # Create and start scheduler
        self.scheduler = LightingScheduler(self.interval_seconds)
        self.scheduler.start()
        
        logger.info(f"Lighting scheduler service started with {self.interval_seconds}s interval")
        
    async def stop_service(self) -> None:
        """
        Stop the lighting scheduler service.
        """
        if not self.scheduler:
            logger.warning("Lighting scheduler service is not running")
            return
            
        self.scheduler.stop()
        await self.scheduler.wait_for_stop()
        
        logger.info("Lighting scheduler service stopped")
        
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status information.
        
        Returns:
            Dictionary containing service status
        """
        if not self.scheduler:
            return {
                "running": False,
                "scheduler": None
            }
            
        return {
            "running": self.scheduler.is_running(),
            "scheduler": self.scheduler.get_status()
        }
        
    def get_runner(self) -> Optional[LightingBehaviorRunner]:
        """
        Get the lighting behavior runner instance.
        
        Returns:
            LightingBehaviorRunner instance or None if not started
        """
        if not self.scheduler:
            return None
        return self.scheduler.get_runner()


# Global service instance
_lighting_scheduler_service: Optional[LightingSchedulerService] = None


def get_lighting_scheduler_service() -> LightingSchedulerService:
    """
    Get the global lighting scheduler service instance.
    
    Returns:
        LightingSchedulerService instance
    """
    global _lighting_scheduler_service
    if _lighting_scheduler_service is None:
        _lighting_scheduler_service = LightingSchedulerService()
    return _lighting_scheduler_service


async def start_lighting_scheduler(interval_seconds: int = 30) -> None:
    """
    Start the global lighting scheduler service.
    
    Args:
        interval_seconds: Interval between runner iterations in seconds
    """
    service = get_lighting_scheduler_service()
    service.interval_seconds = interval_seconds
    await service.start_service()


async def stop_lighting_scheduler() -> None:
    """
    Stop the global lighting scheduler service.
    """
    service = get_lighting_scheduler_service()
    await service.stop_service()


def get_lighting_scheduler_status() -> Dict[str, Any]:
    """
    Get the global lighting scheduler service status.
    
    Returns:
        Dictionary containing service status
    """
    service = get_lighting_scheduler_service()
    return service.get_service_status()


def get_lighting_runner() -> Optional[LightingBehaviorRunner]:
    """
    Get the lighting behavior runner from the global scheduler service.
    
    Returns:
        LightingBehaviorRunner instance or None if not started
    """
    service = get_lighting_scheduler_service()
    return service.get_runner()


# Signal handlers for graceful shutdown
def _signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down lighting scheduler...")
    asyncio.create_task(stop_lighting_scheduler())


# Register signal handlers
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler) 