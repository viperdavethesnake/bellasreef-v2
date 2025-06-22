"""
SmartOutlet Discovery Service

This module provides device discovery functionality for local and cloud-based outlets.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aioshelly

from shared.utils.logger import get_logger
from .drivers.kasa import KasaDriver
from .drivers.shelly import ShellyDriver
from .drivers.vesync import VeSyncDriver
from .exceptions import OutletConnectionError, OutletAuthenticationError, DiscoveryInProgressError, DiscoveryFailedError


class DiscoveryService:
    """
    Service for managing device discovery tasks.
    
    Handles background discovery for local devices (Kasa, Shelly) and
    cloud-based discovery for VeSync devices.
    """
    
    def __init__(self):
        """Initialize the discovery service."""
        self._discovery_results: Dict[str, Dict[str, Any]] = {}
        self._discovery_tasks: Dict[str, asyncio.Task] = {}
        self._logger = get_logger(__name__)
    
    def _cleanup_old_results(self, max_age_hours: int = 24):
        """
        Clean up old discovery results to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age of results to keep
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_tasks = []
        
        for task_id, result in self._discovery_results.items():
            if result.get('created_at', datetime.now()) < cutoff_time:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            self._discovery_results.pop(task_id, None)
            self._discovery_tasks.pop(task_id, None)
    
    async def run_local_discovery(self) -> str:
        """
        Spawn background discovery for local devices (Shelly and Kasa).
        
        Returns:
            str: Task ID for tracking the discovery process
        """
        task_id = str(uuid.uuid4())
        
        # Initialize result structure
        self._discovery_results[task_id] = {
            'status': 'running',
            'created_at': datetime.now(),
            'results': [],
            'error': None
        }
        
        # Create background task
        task = asyncio.create_task(self._run_local_discovery_task(task_id))
        self._discovery_tasks[task_id] = task
        
        # Clean up old results
        self._cleanup_old_results()
        
        return task_id
    
    async def _run_local_discovery_task(self, task_id: str):
        """
        Background task for local device discovery.
        
        Args:
            task_id: The task ID for this discovery operation
        """
        try:
            results = []
            
            # Run Shelly discovery
            try:
                # Use the discover function directly if available
                if hasattr(aioshelly, 'discover'):
                    shelly_devices = await aioshelly.discover()
                    results.extend(shelly_devices)
            except AttributeError:
                # This version of aioshelly doesn't support discovery this way.
                # Log a warning and continue, as the user has no Shelly devices.
                self._logger.warning("aioshelly.discover not found, skipping Shelly discovery.")
            except Exception as e:
                # Log other errors but continue with other drivers
                self._logger.error(f"Error during Shelly discovery: {e}")
            
            # Run Kasa discovery
            try:
                kasa_devices = await KasaDriver.discover_devices()
                results.extend(kasa_devices)
            except Exception as e:
                # Log error but continue
                pass
            
            # Update results
            self._discovery_results[task_id].update({
                'status': 'completed',
                'results': results,
                'completed_at': datetime.now()
            })
            
        except Exception as e:
            # Update results with error
            self._discovery_results[task_id].update({
                'status': 'failed',
                'error': str(e),
                'completed_at': datetime.now()
            })
        finally:
            # Clean up task reference
            self._discovery_tasks.pop(task_id, None)
    
    async def get_discovery_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get discovery results for a specific task.
        
        Args:
            task_id: The task ID to retrieve results for
            
        Returns:
            Optional[Dict]: Discovery results or None if task not found
        """
        return self._discovery_results.get(task_id)
    
    async def run_vesync_discovery(self, email: str, password: str) -> List[Dict[str, Any]]:
        """
        Perform synchronous discovery using VeSync cloud session.
        
        Args:
            email: VeSync account email
            password: VeSync account password
            
        Returns:
            List[Dict]: List of discovered VeSync devices
            
        Raises:
            OutletAuthenticationError: If credentials are invalid
            OutletConnectionError: If discovery fails
        """
        try:
            devices = await VeSyncDriver.discover_devices(email, password)
            return devices
        except OutletAuthenticationError:
            raise
        except Exception as e:
            raise OutletConnectionError(f"VeSync discovery failed: {e}")
    
    def get_active_tasks(self) -> List[str]:
        """
        Get list of active discovery task IDs.
        
        Returns:
            List[str]: List of active task IDs
        """
        return list(self._discovery_tasks.keys())
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running discovery task.
        
        Args:
            task_id: The task ID to cancel
            
        Returns:
            bool: True if task was cancelled, False if not found
        """
        task = self._discovery_tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            return True
        return False 