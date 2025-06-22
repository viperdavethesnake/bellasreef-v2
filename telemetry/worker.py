#!/usr/bin/env python3
"""
Bella's Reef - Telemetry Worker

This is a standalone worker process that polls enabled devices for their
current state and records it in the database history. It runs independently
from the FastAPI application.

Core Logic:
1. Runs in a continuous loop.
2. Fetches all devices with `poll_enabled = true`.
3. For each device, calls the appropriate service API to get data.
4. Stores the result in the `history` table.
5. Handles errors gracefully and updates device status.
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path to allow imports from shared module
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import httpx
from shared.core.config import settings
from shared.db.database import async_session
from shared.crud import device as device_crud
from shared.crud import history as history_crud
from shared.schemas.device import Device, HistoryCreate

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


class TelemetryWorker:
    """
    The main worker class that handles the polling loop and data storage.
    """

    def __init__(self, interval: int):
        self.interval = interval
        self.running = False
        self.client = httpx.AsyncClient(timeout=10.0)
        self.auth_header = {"Authorization": f"Bearer {settings.SERVICE_TOKEN}"}

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals to stop the loop gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def _poll_device(self, device: Device):
        """Polls a single device, gets its data, and stores it."""
        logger.info(f"Polling device: {device.name} (Type: {device.device_type})")
        api_url = ""
        
        # Create a separate session for this polling task
        async with async_session() as session:
            try:
                # Determine the correct API endpoint based on device type
                if device.device_type == 'system_metrics':
                    # Note: This assumes a 'system_metrics' device is pre-configured in your DB
                    # The address would be the Core service URL, e.g., http://localhost:8000
                    api_url = f"{device.address}/api/system-usage"
                elif device.device_type == 'temperature_sensor':
                    # The address for a temp sensor is its hardware ID
                    # We need the temp service URL from settings
                    temp_service_url = f"http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT_TEMP}"
                    api_url = f"{temp_service_url}/probe/{device.address}/current"
                elif device.device_type == 'smart_outlet':
                    # The address for a smart outlet is its database UUID
                    # We need the smartoutlets service URL from settings
                    outlet_service_url = f"http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT_SMARTOUTLETS}"
                    api_url = f"{outlet_service_url}/api/smartoutlets/outlets/{device.address}/state"
                else:
                    logger.warning(f"Unknown device type for polling: {device.device_type}")
                    return

                response = await self.client.get(api_url, headers=self.auth_header)
                response.raise_for_status()  # Will raise an exception for 4xx/5xx responses

                data = response.json()
                history_entry = None

                # Create a HistoryCreate object based on the response shape
                if isinstance(data, dict):
                    history_entry = HistoryCreate(device_id=device.id, json_value=data)
                elif isinstance(data, (int, float)):
                    history_entry = HistoryCreate(device_id=device.id, value=data)
                else:
                    raise ValueError(f"Unexpected data type from API: {type(data)}")

                await history_crud.create(session, obj_in=history_entry)
                await device_crud.update_poll_status(session, device_id=device.id, last_error=None)
                logger.info(f"Successfully recorded history for {device.name}")

            except httpx.RequestError as e:
                error_msg = f"Network error polling {device.name}: {e}"
                logger.error(error_msg)
                await device_crud.update_poll_status(session, device_id=device.id, last_error=error_msg)
            except Exception as e:
                error_msg = f"Failed to poll device {device.name}: {str(e)}"
                logger.error(error_msg)
                
                # Update device polling status on failure
                await device_crud.update_poll_status(session, device_id=device.id, last_error=error_msg)

    async def _run_polling_cycle(self):
        """Runs one full cycle of polling all enabled devices."""
        logger.info("--- Starting new polling cycle ---")
        try:
            # Get pollable devices in a separate session
            async with async_session() as session:
                pollable_devices = await device_crud.get_pollable_devices(session)
            
            if not pollable_devices:
                logger.info("No pollable devices found.")
                return

            logger.info(f"Found {len(pollable_devices)} devices to poll.")
            
            # Create a list of tasks to run concurrently - each task gets its own session
            tasks = [self._poll_device(device) for device in pollable_devices]
            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"Failed to run polling cycle: {e}", exc_info=True)
        logger.info("--- Polling cycle finished ---")

    async def run(self):
        """The main entry point to start the continuous worker loop."""
        self.running = True
        logger.info("Telemetry Worker started. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                await self._run_polling_cycle()
                logger.info(f"Sleeping for {self.interval} seconds...")
                await asyncio.sleep(self.interval)
        finally:
            await self.client.aclose()
            logger.info("HTTP client closed. Telemetry Worker stopped.")


async def main():
    """Parses arguments and runs the worker."""
    parser = argparse.ArgumentParser(description="Bella's Reef Telemetry Worker")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (default: 30)"
    )
    args = parser.parse_args()

    worker = TelemetryWorker(interval=args.interval)
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker process interrupted by user.")
