#!/usr/bin/env python3
"""
Scheduler Worker for Bella's Reef

This is a standalone worker process that manages schedules and creates device actions
on a regular interval. It runs independently from the FastAPI application.

USAGE:
    python backend/app/worker/scheduler_worker.py                    # Run with default settings
    python backend/app/worker/scheduler_worker.py --interval 60      # Run with 60-second interval
    python backend/app/worker/scheduler_worker.py --config-check     # Validate configuration only
    python backend/app/worker/scheduler_worker.py --dry-run          # Run one evaluation cycle and exit

FEATURES:
    - Manages all schedule types (one-off, recurring, interval, cron, static)
    - Creates device actions for due schedules
    - Handles timezone conversions and daylight saving time
    - Comprehensive logging and error handling
    - Configurable evaluation interval
    - Graceful shutdown handling
    - Future-ready for advanced scheduling features

DEPENDENCIES:
    - PostgreSQL database with schedules and device_actions tables
    - .env file with database configuration
    - All required Python packages from requirements.txt
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add the backend directory to Python path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent.parent
sys.path.insert(0, str(backend_dir))

# Import after adding to path
from app.core.config import settings
from app.db.base import async_session
from app.worker.schedule_calculator import ScheduleCalculator
from app.crud.schedule import schedule as schedule_crud
from app.schemas.schedule import ScheduleCreate, ActionTypeEnum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scheduler_worker.log')
    ]
)

logger = logging.getLogger(__name__)

class SchedulerWorker:
    """
    Standalone scheduler worker process.
    
    This worker runs continuously, checking for due schedules at regular intervals
    and creating device actions in the database. It's designed to be independent
    of the FastAPI application and can be run as a separate process or service.
    """
    
    def __init__(self, evaluation_interval: int = 30):
        """
        Initialize the scheduler worker.
        
        Args:
            evaluation_interval: Seconds between evaluation cycles (default: 30)
        """
        self.evaluation_interval = evaluation_interval
        self.running = False
        self.stats = {
            "cycles": 0,
            "total_schedules_processed": 0,
            "total_actions_created": 0,
            "total_errors": 0,
            "start_time": None,
            "last_evaluation": None
        }
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _check_configuration(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        logger.info("Checking configuration...")
        
        # Check required settings
        required_settings = {
            "DATABASE_URL": settings.DATABASE_URL,
            "POSTGRES_SERVER": settings.POSTGRES_SERVER,
            "POSTGRES_DB": settings.POSTGRES_DB,
            "POSTGRES_USER": settings.POSTGRES_USER,
        }
        
        missing_settings = []
        for name, value in required_settings.items():
            if not value or value.strip() == "":
                missing_settings.append(name)
        
        if missing_settings:
            logger.error(f"Missing required settings: {missing_settings}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def _test_database_connection(self) -> bool:
        """
        Test database connection and verify required tables exist.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            async def test_connection():
                async with async_session() as db:
                    # Test connection by executing a simple query
                    result = await db.execute("SELECT 1")
                    if result.scalar() != 1:
                        raise Exception("Database connection test failed")
                    
                    # Check if required tables exist
                    tables = ["schedules", "device_actions", "devices"]
                    for table in tables:
                        result = await db.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                        if not result.scalar():
                            logger.error(f"Required table '{table}' does not exist")
                            return False
                    
                    logger.info("Database connection and table verification successful")
                    return True
            
            # Run the async test
            import asyncio
            return asyncio.run(test_connection())
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def _create_static_schedules(self) -> bool:
        """
        Create default static schedules if they don't exist.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            async def create_schedules():
                async with async_session() as db:
                    # Check if static schedules already exist
                    existing_static = await schedule_crud.get_static_schedules(db)
                    if existing_static:
                        logger.info(f"Found {len(existing_static)} existing static schedules")
                        return True
                    
                    logger.info("Creating default static schedules...")
                    
                    # Create diurnal light cycle schedule
                    light_schedule = ScheduleCreate(
                        name="Diurnal Light Cycle",
                        device_ids=[],  # Will be populated when devices are available
                        schedule_type="static",
                        start_time=datetime.now(timezone.utc).replace(hour=6, minute=0, second=0, microsecond=0),
                        timezone="UTC",
                        is_enabled=True,
                        action_type=ActionTypeEnum.SET_PWM,
                        action_params={
                            "target": 100,
                            "duration": 3600,  # 1 hour ramp
                            "description": "Sunrise to peak lighting"
                        }
                    )
                    
                    await schedule_crud.create(db, light_schedule)
                    logger.info("Created diurnal light cycle schedule")
                    
                    # Create sunset schedule
                    sunset_schedule = ScheduleCreate(
                        name="Sunset Lighting",
                        device_ids=[],  # Will be populated when devices are available
                        schedule_type="static",
                        start_time=datetime.now(timezone.utc).replace(hour=18, minute=0, second=0, microsecond=0),
                        timezone="UTC",
                        is_enabled=True,
                        action_type=ActionTypeEnum.RAMP,
                        action_params={
                            "start_level": 100,
                            "end_level": 0,
                            "duration": 3600,  # 1 hour ramp down
                            "description": "Sunset lighting ramp down"
                        }
                    )
                    
                    await schedule_crud.create(db, sunset_schedule)
                    logger.info("Created sunset lighting schedule")
                    
                    return True
            
            # Run the async creation
            import asyncio
            return asyncio.run(create_schedules())
            
        except Exception as e:
            logger.error(f"Error creating static schedules: {e}")
            return False
    
    def _run_evaluation_cycle(self) -> bool:
        """
        Run a single evaluation cycle.
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        try:
            async def run_cycle():
                async with async_session() as db:
                    calculator = ScheduleCalculator(db)
                    
                    logger.info(f"Starting evaluation cycle {self.stats['cycles'] + 1}")
                    cycle_start = time.time()
                    
                    # Process due schedules
                    result = await calculator.process_due_schedules()
                    
                    # Update statistics
                    self.stats["cycles"] += 1
                    self.stats["total_schedules_processed"] += result.get("processed", 0)
                    self.stats["total_actions_created"] += result.get("actions_created", 0)
                    self.stats["total_errors"] += result.get("errors", 0)
                    self.stats["last_evaluation"] = time.time()
                    
                    cycle_duration = time.time() - cycle_start
                    logger.info(f"Evaluation cycle completed in {cycle_duration:.2f}s: {result}")
                    
                    return True
            
            # Run the async cycle
            import asyncio
            return asyncio.run(run_cycle())
            
        except Exception as e:
            logger.error(f"Error during evaluation cycle: {e}")
            self.stats["total_errors"] += 1
            return False
    
    def _print_stats(self):
        """Print current worker statistics."""
        if self.stats["start_time"]:
            uptime = time.time() - self.stats["start_time"]
            logger.info(f"Worker Statistics:")
            logger.info(f"  Uptime: {uptime:.1f} seconds")
            logger.info(f"  Cycles: {self.stats['cycles']}")
            logger.info(f"  Schedules Processed: {self.stats['total_schedules_processed']}")
            logger.info(f"  Actions Created: {self.stats['total_actions_created']}")
            logger.info(f"  Errors: {self.stats['total_errors']}")
            if self.stats["last_evaluation"]:
                last_eval = time.time() - self.stats["last_evaluation"]
                logger.info(f"  Last Evaluation: {last_eval:.1f} seconds ago")
    
    def run(self, dry_run: bool = False):
        """
        Run the scheduler worker.
        
        Args:
            dry_run: If True, run one evaluation cycle and exit
        """
        logger.info("Starting Bella's Reef Scheduler Worker")
        logger.info(f"Evaluation interval: {self.evaluation_interval} seconds")
        
        # Check configuration
        if not self._check_configuration():
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Test database connection
        if not self._test_database_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        # Create static schedules if needed
        if not self._create_static_schedules():
            logger.warning("Failed to create static schedules, continuing anyway")
        
        self.running = True
        self.stats["start_time"] = time.time()
        
        try:
            if dry_run:
                logger.info("Running in dry-run mode (single evaluation cycle)")
                self._run_evaluation_cycle()
                self._print_stats()
                logger.info("Dry run completed")
                return
            
            logger.info("Starting continuous evaluation loop...")
            logger.info("Press Ctrl+C to stop gracefully")
            
            while self.running:
                cycle_start = time.time()
                
                # Run evaluation cycle
                success = self._run_evaluation_cycle()
                
                if not success:
                    logger.warning("Evaluation cycle failed, will retry on next interval")
                
                # Calculate sleep time
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, self.evaluation_interval - cycle_duration)
                
                if sleep_time > 0:
                    logger.debug(f"Sleeping for {sleep_time:.1f} seconds")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.running = False
            self._print_stats()
            logger.info("Scheduler worker stopped")


def main():
    """Main entry point for the scheduler worker."""
    parser = argparse.ArgumentParser(
        description="Bella's Reef Scheduler Worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="Evaluation interval in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run one evaluation cycle and exit"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run worker
    worker = SchedulerWorker(evaluation_interval=args.interval)
    
    if args.config_check:
        logger.info("Configuration check mode")
        if worker._check_configuration() and worker._test_database_connection():
            logger.info("Configuration validation passed")
            sys.exit(0)
        else:
            logger.error("Configuration validation failed")
            sys.exit(1)
    
    worker.run(dry_run=args.dry_run)


if __name__ == "__main__":
    main() 