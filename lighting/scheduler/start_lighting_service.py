#!/usr/bin/env python3
"""
Lighting Service Startup Script.

This script starts the lighting behavior scheduler as a standalone service.
It can be run independently or integrated into the main BellasReef application.

Usage:
    python start_lighting_service.py [--interval SECONDS] [--log-level LEVEL]
"""
import asyncio
import argparse
import signal
import sys
import os
from datetime import datetime
from typing import Optional
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.utils.logger import get_logger
from lighting.scheduler.lighting_scheduler import (
    get_lighting_scheduler_service,
    start_lighting_scheduler,
    stop_lighting_scheduler
)

logger = get_logger(__name__)


class LightingServiceRunner:
    """
    Runner for the lighting service.
    
    This class manages the lifecycle of the lighting scheduler service,
    including startup, shutdown, and signal handling.
    """
    
    def __init__(self, interval_seconds: int = 30, log_level: str = "INFO"):
        """
        Initialize the lighting service runner.
        
        Args:
            interval_seconds: Interval between runner iterations in seconds
            log_level: Logging level
        """
        self.interval_seconds = interval_seconds
        self.log_level = log_level
        self.running = False
        
        # Setup logging using get_logger
        self.logger = get_logger(__name__, level=getattr(logging, log_level.upper()))
        
    async def start(self) -> None:
        """
        Start the lighting service.
        """
        try:
            self.logger.info("Starting BellasReef Lighting Service...")
            self.logger.info(f"Configuration: interval={self.interval_seconds}s, log_level={self.log_level}")
            
            # Start the lighting scheduler
            await start_lighting_scheduler(self.interval_seconds)
            
            self.running = True
            self.logger.info("BellasReef Lighting Service started successfully")
            
            # Keep the service running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            self.logger.error(f"Error in lighting service: {e}")
            raise
        finally:
            await self.stop()
            
    async def stop(self) -> None:
        """
        Stop the lighting service.
        """
        if not self.running:
            return
            
        self.logger.info("Stopping BellasReef Lighting Service...")
        
        try:
            # Stop the lighting scheduler
            await stop_lighting_scheduler()
            
            self.running = False
            self.logger.info("BellasReef Lighting Service stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping lighting service: {e}")
            
    def signal_handler(self, signum, frame):
        """
        Handle shutdown signals.
        """
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


async def main():
    """
    Main entry point for the lighting service.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="BellasReef Lighting Service")
    parser.add_argument(
        "--interval", 
        type=int, 
        default=30,
        help="Interval between runner iterations in seconds (default: 30)"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Validate interval
    if args.interval < 5:
        logger.error("Interval must be at least 5 seconds")
        sys.exit(1)
    if args.interval > 3600:
        logger.error("Interval must be at most 3600 seconds (1 hour)")
        sys.exit(1)
    
    # Create and run the service
    runner = LightingServiceRunner(args.interval, args.log_level)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    try:
        await runner.start()
    except Exception as e:
        logger.error(f"Failed to start lighting service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 