#!/usr/bin/env python3
"""
Alert Worker for Bella's Reef

This is a standalone worker process that evaluates alerts against device readings
on a regular interval. It runs independently from the FastAPI application.

USAGE:
    python backend/app/worker/alert_worker.py                    # Run with default settings
    python backend/app/worker/alert_worker.py --interval 60      # Run with 60-second interval
    python backend/app/worker/alert_worker.py --config-check     # Validate configuration only
    python backend/app/worker/alert_worker.py --dry-run          # Run one evaluation cycle and exit

FEATURES:
    - Evaluates all enabled alerts against latest device readings
    - Creates alert events when thresholds are exceeded
    - Resolves alerts when conditions return to normal
    - Comprehensive logging and error handling
    - Configurable evaluation interval
    - Graceful shutdown handling
    - Future-ready for trend analysis and notifications

DEPENDENCIES:
    - PostgreSQL database with alerts, devices, and history tables
    - .env file with database configuration
    - All required Python packages from requirements.txt
"""

import argparse
import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Add the backend directory to Python path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent.parent
sys.path.insert(0, str(backend_dir))

# Import after adding to path
from app.core.config import settings
from app.db.base import async_session
from app.worker.alert_evaluator import AlertEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('alert_worker.log')
    ]
)

logger = logging.getLogger(__name__)

class AlertWorker:
    """
    Standalone alert evaluation worker.
    
    This worker runs continuously, evaluating alerts at regular intervals.
    It's designed to be independent of the FastAPI application and can be
    run as a separate process or service.
    """
    
    def __init__(self, evaluation_interval: int = 30):
        """
        Initialize the alert worker.
        
        Args:
            evaluation_interval: Seconds between evaluation cycles (default: 30)
        """
        self.evaluation_interval = evaluation_interval
        self.running = False
        self.stats = {
            "cycles": 0,
            "total_alerts_evaluated": 0,
            "total_alerts_triggered": 0,
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
                    tables = ["alerts", "devices", "history", "alert_events"]
                    for table in tables:
                        result = await db.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                        if not result.scalar():
                            logger.error(f"Required table '{table}' does not exist")
                            return False
                    
                    logger.info("Database connection and table verification successful")
                    return True
            
            # Run the async test
            return asyncio.run(test_connection())
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
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
                    evaluator = AlertEvaluator(db)
                    
                    logger.info(f"Starting evaluation cycle {self.stats['cycles'] + 1}")
                    cycle_start = time.time()
                    
                    # Run the evaluation
                    result = await evaluator.evaluate_all_alerts()
                    
                    # Update statistics
                    self.stats["cycles"] += 1
                    self.stats["total_alerts_evaluated"] += result.get("evaluated", 0)
                    self.stats["total_alerts_triggered"] += result.get("triggered", 0)
                    self.stats["total_errors"] += result.get("errors", 0)
                    self.stats["last_evaluation"] = time.time()
                    
                    cycle_duration = time.time() - cycle_start
                    logger.info(f"Evaluation cycle completed in {cycle_duration:.2f}s: {result}")
                    
                    return True
            
            # Run the async cycle
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
            logger.info(f"  Alerts Evaluated: {self.stats['total_alerts_evaluated']}")
            logger.info(f"  Alerts Triggered: {self.stats['total_alerts_triggered']}")
            logger.info(f"  Errors: {self.stats['total_errors']}")
            if self.stats["last_evaluation"]:
                last_eval = time.time() - self.stats["last_evaluation"]
                logger.info(f"  Last Evaluation: {last_eval:.1f} seconds ago")
    
    def run(self, dry_run: bool = False):
        """
        Run the alert worker.
        
        Args:
            dry_run: If True, run one evaluation cycle and exit
        """
        logger.info("Starting Bella's Reef Alert Worker")
        logger.info(f"Evaluation interval: {self.evaluation_interval} seconds")
        
        # Check configuration
        if not self._check_configuration():
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Test database connection
        if not self._test_database_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
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
            logger.info("Alert worker stopped")


def main():
    """Main entry point for the alert worker."""
    parser = argparse.ArgumentParser(
        description="Bella's Reef Alert Worker",
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
    worker = AlertWorker(evaluation_interval=args.interval)
    
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