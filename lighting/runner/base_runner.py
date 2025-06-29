"""
Lighting Behavior Runner.

This module provides the core runner for executing lighting behaviors,
including intensity calculation, effect/override processing, and hardware integration.
All operations use the real HAL layer for hardware control.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

from shared.utils.logger import get_logger
from lighting.runner.intensity_calculator import IntensityCalculator
from lighting.engine.queue_manager import QueueManager
from hal.services.lighting_service import get_lighting_hal_service

logger = get_logger(__name__)


class LightingBehaviorRunner:
    """
    Runner for executing lighting behaviors.
    
    This runner:
    - Fetches active behavior assignments
    - Calculates desired intensities based on behaviors
    - Applies effects and overrides
    - Writes to hardware through HAL
    - Manages channel registration
    - Provides status monitoring
    """
    
    def __init__(self, behavior_manager):
        """
        Initialize the lighting behavior runner.
        
        Args:
            behavior_manager: Behavior manager instance for fetching assignments
        """
        self.behavior_manager = behavior_manager
        
        # Initialize components
        self.intensity_calculator = IntensityCalculator()
        self.queue_manager = QueueManager()
        
        # Initialize HAL service (real hardware only)
        self.hal_service = get_lighting_hal_service()
        
        # Channel registration tracking
        self._registered_channels: Dict[int, Dict[str, Any]] = {}
        
        # Log initialization
        self._log_execution_status("runner_init", hal_mode="real")
        logger.info("Lighting behavior runner initialized with real HAL layer")
        
    def register_channel(
        self, 
        channel_id: int, 
        controller_address: int, 
        channel_number: int,
        min_value: float = 0.0,
        max_value: float = 100.0
    ) -> bool:
        """
        Register a lighting channel with the HAL service.
        
        Args:
            channel_id: Lighting system channel identifier
            controller_address: I2C address of the PCA9685 controller (0x40-0x7F)
            channel_number: Channel number on the controller (0-15)
            min_value: Minimum physical value for the channel (0.0-100.0)
            max_value: Maximum physical value for the channel (0.0-100.0)
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate inputs
            if not 0 <= channel_number <= 15:
                logger.error(f"Invalid channel number: {channel_number} (must be 0-15)")
                return False
                
            if not 0x40 <= controller_address <= 0x7F:
                logger.error(f"Invalid controller address: {hex(controller_address)} (must be 0x40-0x7F)")
                return False
            
            # Validate min/max values
            if not isinstance(min_value, (int, float)) or not isinstance(max_value, (int, float)):
                logger.error(f"Invalid min/max values: min={min_value}, max={max_value} (must be numbers)")
                return False
                
            if min_value < 0.0 or max_value > 100.0:
                logger.error(f"Invalid min/max values: min={min_value}, max={max_value} (must be 0.0-100.0)")
                return False
                
            if min_value >= max_value:
                logger.error(f"Invalid min/max values: min={min_value} must be less than max={max_value}")
                return False
            
            # Register with HAL service
            success = self.hal_service.register_channel(channel_id, controller_address, channel_number)
            
            if success:
                # Track registration locally with min/max values
                self._registered_channels[channel_id] = {
                    "controller_address": controller_address,
                    "channel_number": channel_number,
                    "min_value": min_value,
                    "max_value": max_value,
                    "registered_at": datetime.utcnow()
                }
                
                logger.info(f"Channel {channel_id} registered: I2C:{hex(controller_address)} Ch:{channel_number} Range:{min_value}-{max_value}")
                self._log_execution_status("channel_registered", channel_id=channel_id)
                return True
            else:
                logger.error(f"Failed to register channel {channel_id} with HAL service")
                return False
                
        except Exception as e:
            logger.error(f"Error registering channel {channel_id}: {e}")
            return False
            
    def unregister_channel(self, channel_id: int) -> bool:
        """
        Unregister a lighting channel from the HAL service.
        
        Args:
            channel_id: Lighting system channel identifier
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if channel_id not in self._registered_channels:
                logger.warning(f"Channel {channel_id} not registered")
                return False
            
            # Unregister from HAL service
            success = self.hal_service.unregister_channel(channel_id)
            
            if success:
                # Remove from local tracking
                del self._registered_channels[channel_id]
                
                logger.info(f"Channel {channel_id} unregistered")
                self._log_execution_status("channel_unregistered", channel_id=channel_id)
                return True
            else:
                logger.error(f"Failed to unregister channel {channel_id} from HAL service")
                return False
                
        except Exception as e:
            logger.error(f"Error unregistering channel {channel_id}: {e}")
            return False
            
    def get_registered_channels(self) -> List[int]:
        """
        Get list of registered channel IDs.
        
        Returns:
            List of registered channel IDs
        """
        return list(self._registered_channels.keys())
        
    def get_channel_status(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed status for a specific channel.
        
        Args:
            channel_id: Channel identifier
            
        Returns:
            Channel status information or None if not found
        """
        if channel_id not in self._registered_channels:
            return None
            
        try:
            # Get current intensity from hardware
            current_intensity = self.hal_service.read_channel_intensity(channel_id)
            
            # Get queue status for this channel
            queue_status = self.queue_manager.get_channel_queue_status(channel_id, datetime.utcnow())
            
            return {
                "channel_id": channel_id,
                "registration": self._registered_channels[channel_id],
                "current_intensity": current_intensity,
                "queue_status": queue_status,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting status for channel {channel_id}: {e}")
            return None
            
    def add_effect(
        self,
        effect_type: str,
        channels: List[int],
        parameters: Dict[str, Any],
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60,
        priority: int = 1
    ) -> Optional[str]:
        """
        Add an effect to the effect queue.
        
        Args:
            effect_type: Type of effect to apply
            channels: List of channel IDs to apply effect to
            parameters: Effect parameters
            start_time: When to start the effect (defaults to now)
            duration_minutes: How long the effect should last
            priority: Effect priority (higher = more important)
            
        Returns:
            Effect ID if successful, None otherwise
        """
        try:
            # Validate channels are registered
            unregistered_channels = [ch_id for ch_id in channels if ch_id not in self._registered_channels]
            if unregistered_channels:
                logger.error(f"Cannot add effect: channels not registered: {unregistered_channels}")
                return None
            
            # Add to queue
            effect_id = self.queue_manager.add_effect(
                effect_type=effect_type,
                channels=channels,
                parameters=parameters,
                start_time=start_time or datetime.utcnow(),
                duration_minutes=duration_minutes,
                priority=priority
            )
            
            if effect_id:
                logger.info(f"Effect added: {effect_type} on channels {channels}")
                self._log_execution_status("effect_added", effect_id=effect_id, channels=channels)
                
            return effect_id
            
        except Exception as e:
            logger.error(f"Error adding effect: {e}")
            return None
            
    def remove_effect(self, effect_id: str) -> bool:
        """
        Remove an effect from the effect queue.
        
        Args:
            effect_id: ID of effect to remove
            
        Returns:
            True if removal successful, False otherwise
        """
        try:
            success = self.queue_manager.remove_effect(effect_id)
            
            if success:
                logger.info(f"Effect removed: {effect_id}")
                self._log_execution_status("effect_removed", effect_id=effect_id)
                
            return success
            
        except Exception as e:
            logger.error(f"Error removing effect {effect_id}: {e}")
            return False
            
    def add_override(
        self,
        override_type: str,
        channels: List[int],
        intensity: float,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60,
        priority: int = 10,
        reason: Optional[str] = None
    ) -> Optional[str]:
        """
        Add an override to the override queue.
        
        Args:
            override_type: Type of override to apply
            channels: List of channel IDs to apply override to
            intensity: Override intensity (0.0-1.0)
            start_time: When to start the override (defaults to now)
            duration_minutes: How long the override should last
            priority: Override priority (higher = more important)
            reason: Reason for the override
            
        Returns:
            Override ID if successful, None otherwise
        """
        try:
            # Validate intensity
            if not 0.0 <= intensity <= 1.0:
                logger.error(f"Invalid override intensity: {intensity} (must be 0.0-1.0)")
                return None
            
            # Validate channels are registered
            unregistered_channels = [ch_id for ch_id in channels if ch_id not in self._registered_channels]
            if unregistered_channels:
                logger.error(f"Cannot add override: channels not registered: {unregistered_channels}")
                return None
            
            # Add to queue
            override_id = self.queue_manager.add_override(
                override_type=override_type,
                channels=channels,
                intensity=intensity,
                start_time=start_time or datetime.utcnow(),
                duration_minutes=duration_minutes,
                priority=priority,
                reason=reason
            )
            
            if override_id:
                logger.info(f"Override added: {override_type} intensity {intensity} on channels {channels}")
                self._log_execution_status("override_added", override_id=override_id, channels=channels)
                
            return override_id
            
        except Exception as e:
            logger.error(f"Error adding override: {e}")
            return None
            
    def remove_override(self, override_id: str) -> bool:
        """
        Remove an override from the override queue.
        
        Args:
            override_id: ID of override to remove
            
        Returns:
            True if removal successful, False otherwise
        """
        try:
            success = self.queue_manager.remove_override(override_id)
            
            if success:
                logger.info(f"Override removed: {override_id}")
                self._log_execution_status("override_removed", override_id=override_id)
                
            return success
            
        except Exception as e:
            logger.error(f"Error removing override {override_id}: {e}")
            return False
            
    async def run_iteration(self) -> Dict[int, float]:
        """
        Run a single iteration of the behavior runner.
        
        This method:
        1. Fetches active behavior assignments
        2. Calculates desired intensities
        3. Applies effects and overrides
        4. Writes to hardware through HAL
        
        Returns:
            Dictionary mapping channel_id to final intensity
        """
        try:
            current_time = datetime.utcnow()
            
            # Get active assignments
            active_assignments = self.behavior_manager.get_active_assignments(current_time)
            
            # Calculate base intensities from behaviors
            base_intensities = {}
            for assignment in active_assignments:
                channel_id = assignment.get("channel_id")
                if channel_id and channel_id in self._registered_channels:
                    behavior = self.behavior_manager.get_behavior(assignment.get("behavior_id"))
                    if behavior:
                        intensity = await self.intensity_calculator.calculate_intensity(
                            behavior=behavior,
                            assignment=assignment,
                            current_time=current_time
                        )
                        base_intensities[channel_id] = intensity
            
            # Apply effects
            effect_intensities = self.queue_manager.apply_effects(
                base_intensities, 
                current_time
            )
            
            # Apply overrides
            final_intensities = self.queue_manager.apply_overrides(
                effect_intensities, 
                current_time
            )
            
            # Write to hardware
            successful_writes = {}
            for channel_id, intensity in final_intensities.items():
                if channel_id in self._registered_channels:
                    # Get min/max values for this channel
                    channel_config = self._registered_channels[channel_id]
                    min_value = channel_config.get("min_value", 0.0)
                    max_value = channel_config.get("max_value", 100.0)
                    
                    # Map logical intensity (0.0-1.0) to physical intensity percentage
                    physical_intensity_percent = min_value + (max_value - min_value) * intensity
                    
                    # Convert percentage back to 0.0-1.0 float for HAL service
                    final_intensity_for_hal = physical_intensity_percent / 100.0
                    
                    success = self.hal_service.write_channel_intensity(
                        channel_id, 
                        final_intensity_for_hal, 
                        {"runner": "iteration", "timestamp": current_time.isoformat()}
                    )
                    if success:
                        successful_writes[channel_id] = intensity
                    else:
                        logger.error(f"Failed to write intensity {final_intensity_for_hal} to channel {channel_id}")
            
            # Log execution
            self._log_execution_status(
                "iteration_completed",
                channels_processed=len(successful_writes),
                total_assignments=len(active_assignments)
            )
            
            return successful_writes
            
        except Exception as e:
            logger.error(f"Error in runner iteration: {e}")
            self._log_execution_status("iteration_error", error=str(e))
            return {}
            
    def get_hardware_status(self) -> Dict[str, Any]:
        """
        Get hardware status information.
        
        Returns:
            Dictionary containing hardware status
        """
        try:
            hal_status = self.hal_service.get_status()
            
            return {
                "registered_channels": len(self._registered_channels),
                "channel_details": self._registered_channels,
                "hal_status": hal_status,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting hardware status: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
            
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current status of effect and override queues.
        
        Returns:
            Dictionary containing queue status
        """
        try:
            current_time = datetime.utcnow()
            
            return {
                "effects": self.queue_manager.get_active_effects(current_time),
                "overrides": self.queue_manager.get_active_overrides(current_time),
                "timestamp": current_time
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
            
    def cleanup_expired_entries(self) -> Dict[str, int]:
        """
        Clean up expired effects and overrides.
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            current_time = datetime.utcnow()
            
            effects_cleaned = self.queue_manager.cleanup_expired_effects(current_time)
            overrides_cleaned = self.queue_manager.cleanup_expired_overrides(current_time)
            
            result = {
                "effects_cleaned": effects_cleaned,
                "overrides_cleaned": overrides_cleaned,
                "timestamp": current_time
            }
            
            if effects_cleaned > 0 or overrides_cleaned > 0:
                logger.info(f"Cleanup completed: {effects_cleaned} effects, {overrides_cleaned} overrides")
                self._log_execution_status("cleanup_completed", **result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {
                "effects_cleaned": 0,
                "overrides_cleaned": 0,
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
            
    def _log_execution_status(self, status: str, **kwargs) -> None:
        """
        Log execution status through the behavior manager.
        
        Args:
            status: Status message
            **kwargs: Additional context data
        """
        try:
            # Create log entry
            log_data = {
                "status": status,
                "timestamp": datetime.utcnow(),
                "runner_mode": "real",
                **kwargs
            }
            
            # Log through behavior manager
            # TODO: Implement actual logging through behavior manager
            # For now, just log to console
            logger.info(f"RUNNER_LOG: {status} - {kwargs}")
            
        except Exception as e:
            logger.error(f"Failed to log execution status {status}: {e}") 