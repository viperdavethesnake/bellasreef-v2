"""
Override queue for lighting behaviors.

This module provides the override queue system for managing temporary
lighting overrides that take precedence over base behaviors.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from lighting.models.schemas import LightingBehaviorType, LightingBehavior, LightingBehaviorAssignment
from lighting.runner.intensity_calculator import IntensityCalculator


class OverrideEntry:
    """
    Represents an override in the override queue.
    """

    def __init__(
        self,
        override_id: str,
        override_type: str,
        channels: List[int],
        intensity: float,
        start_time: datetime,
        duration_minutes: int,
        priority: int = 10,
        reason: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an override entry.
        
        Args:
            override_id: Unique override identifier
            override_type: Type of override (manual, emergency, maintenance, etc.)
            channels: List of channel IDs affected
            intensity: Target intensity (0.0-1.0)
            start_time: When the override should start (UTC)
            duration_minutes: How long the override should last
            priority: Override priority (higher = more important)
            reason: Reason for the override
            parameters: Additional parameters for complex overrides
        """
        self.override_id = override_id
        self.override_type = override_type
        self.channels = channels
        self.intensity = max(0.0, min(1.0, intensity))  # Clamp to valid range
        self.start_time = start_time
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.reason = reason
        self.created_at = datetime.utcnow()
        self.parameters = parameters or {}
        
        # TODO: Add override validation
        # TODO: Add intensity validation
        # TODO: Add channel validation

    def is_active(self, current_time: datetime) -> bool:
        """
        Check if the override is currently active.
        
        Args:
            current_time: Current UTC time
            
        Returns:
            True if override is active
        """
        end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        return self.start_time <= current_time <= end_time

    def get_progress(self, current_time: datetime) -> float:
        """
        Get the progress of the override (0.0-1.0).
        
        Args:
            current_time: Current UTC time
            
        Returns:
            Progress value (0.0-1.0)
        """
        if not self.is_active(current_time):
            return 0.0
            
        total_duration = self.duration_minutes * 60  # seconds
        elapsed = (current_time - self.start_time).total_seconds()
        
        return min(1.0, elapsed / total_duration)

    def get_override_intensity(self, current_time: datetime) -> float:
        """
        Get the override intensity for the current time.
        
        Args:
            current_time: Current UTC time
            
        Returns:
            Override intensity value (0.0-1.0)
        """
        if not self.is_active(current_time):
            return 0.0
            
        # Check if override has fade-in/fade-out
        fade_duration = self.parameters.get("fade_duration", 0)  # minutes
        
        if fade_duration > 0:
            progress = self.get_progress(current_time)
            total_duration = self.duration_minutes
            
            if progress <= fade_duration / total_duration:
                # Fade in
                fade_progress = progress * total_duration / fade_duration
                return self.intensity * fade_progress
            elif progress >= 1.0 - fade_duration / total_duration:
                # Fade out
                fade_progress = (1.0 - progress) * total_duration / fade_duration
                return self.intensity * fade_progress
            else:
                # Full intensity
                return self.intensity
        else:
            # No fade - constant intensity
            return self.intensity

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get override parameters (for compatibility with effect system)."""
        return {
            "fade_duration": 0,  # Default no fade
            "override_type": self.override_type,
            "reason": self.reason,
        }


class OverrideQueue:
    """
    Queue for managing lighting overrides.
    
    This class manages a queue of overrides that take precedence over
    base behaviors and effects. Overrides are processed in priority order
    and can overlap in time.
    
    TODO: Add override persistence
    TODO: Add override scheduling
    TODO: Add override monitoring
    TODO: Add override cleanup
    """

    def __init__(self):
        """Initialize the override queue."""
        self.overrides: List[OverrideEntry] = []
        self.next_override_id = 1
        
        # TODO: Initialize override storage
        # TODO: Initialize override scheduler
        # TODO: Initialize override monitor

    def add_override(
        self,
        override_type: str,
        channels: List[int],
        intensity: float,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60,
        priority: int = 10,
        reason: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an override to the queue.
        
        Args:
            override_type: Type of override
            channels: List of channel IDs affected
            intensity: Target intensity (0.0-1.0)
            start_time: When to start (defaults to now)
            duration_minutes: How long to run
            priority: Override priority
            reason: Reason for the override
            parameters: Additional parameters for complex overrides
            
        Returns:
            Override ID
            
        Raises:
            ValueError: If there's a channel conflict with existing overrides
        """
        if start_time is None:
            start_time = datetime.utcnow()
            
        # Check for channel conflicts with existing active overrides
        current_time = datetime.utcnow()
        active_overrides = self.get_active_overrides(current_time)
        for active_override in active_overrides:
            # Check if any channels overlap
            overlapping_channels = set(channels) & set(active_override.channels)
            if overlapping_channels:
                raise ValueError(
                    f"Channel conflict: channels {list(overlapping_channels)} are already "
                    f"part of active override {active_override.override_id} ({active_override.override_type})"
                )
        
        override_id = f"override_{self.next_override_id}"
        self.next_override_id += 1
        
        override = OverrideEntry(
            override_id=override_id,
            override_type=override_type,
            channels=channels,
            intensity=intensity,
            start_time=start_time,
            duration_minutes=duration_minutes,
            priority=priority,
            reason=reason,
            parameters=parameters,
        )
        
        self.overrides.append(override)
        return override_id

    def remove_override(self, override_id: str) -> bool:
        """
        Remove an override from the queue.
        
        Args:
            override_id: ID of override to remove
            
        Returns:
            True if override was removed, False if not found
        """
        for i, override in enumerate(self.overrides):
            if override.override_id == override_id:
                del self.overrides[i]
                return True
        return False

    def get_active_overrides(
        self, current_time: Optional[datetime] = None
    ) -> List[OverrideEntry]:
        """
        Get all currently active overrides.
        
        Args:
            current_time: Current UTC time (defaults to now)
            
        Returns:
            List of active overrides
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        return [override for override in self.overrides if override.is_active(current_time)]

    def get_channel_overrides(
        self, channel_id: int, current_time: Optional[datetime] = None
    ) -> List[OverrideEntry]:
        """
        Get all overrides affecting a specific channel.
        
        Args:
            channel_id: Channel ID
            current_time: Current UTC time (defaults to now)
            
        Returns:
            List of overrides affecting the channel
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        return [
            override for override in self.overrides 
            if channel_id in override.channels and override.is_active(current_time)
        ]

    def apply_overrides(
        self, intensities: Dict[int, float], current_time: Optional[datetime] = None
    ) -> Dict[int, float]:
        """
        Apply all active overrides to intensities.
        
        Args:
            intensities: Intensity values per channel (from effects or base)
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Final intensity values with overrides applied
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Start with input intensities
        result_intensities = intensities.copy()
        
        # Get active overrides sorted by priority (highest first)
        active_overrides = sorted(
            self.get_active_overrides(current_time),
            key=lambda x: x.priority,
            reverse=True
        )
        
        # This will hold channel_ids that are already controlled by a higher-priority preview
        preview_controlled_channels = set()
        
        # Apply each override to its channels
        for override in active_overrides:
            if override.override_type == "DayPreview":
                # Handle the Day Preview Simulation
                if not override.parameters or "assignments" not in override.parameters:
                    continue

                # Calculate real-time progress of the preview (0.0 to 1.0)
                elapsed_seconds = (current_time - override.start_time).total_seconds()
                total_duration_seconds = override.duration_minutes * 60
                progress = min(elapsed_seconds / total_duration_seconds, 1.0)

                # Map progress to a 24-hour clock starting at 6 AM
                simulated_hour = (6 + (progress * 24)) % 24
                simulated_time = current_time.replace(hour=int(simulated_hour), minute=int((simulated_hour % 1) * 60))

                # For now, use a simplified calculation since we can't call async methods here
                # In a production system, this would need to be handled differently
                for assignment_data in override.parameters["assignments"]:
                    channel_id = assignment_data["channel_id"]
                    
                    # Use a simple time-based intensity calculation for preview
                    # This simulates a basic day/night cycle
                    hour = simulated_time.hour
                    if 6 <= hour <= 18:  # Daytime (6 AM to 6 PM)
                        # Peak at noon, fade at edges
                        peak_hour = 12
                        intensity = 1.0 - abs(hour - peak_hour) / 6.0
                        intensity = max(0.1, min(1.0, intensity))
                    else:  # Nighttime
                        intensity = 0.1
                    
                    result_intensities[channel_id] = intensity
                    preview_controlled_channels.add(channel_id)

            else:
                # Handle normal, fixed-intensity overrides
                override_intensity = override.get_override_intensity(current_time)
                
                # Apply override to all affected channels (overrides replace the intensity)
                for channel_id in override.channels:
                    # Do not apply if already handled by a higher-priority preview
                    if channel_id not in preview_controlled_channels:
                        result_intensities[channel_id] = override_intensity
        
        return result_intensities

    def cleanup_expired_overrides(self, current_time: Optional[datetime] = None) -> int:
        """
        Remove expired overrides from the queue.
        
        Args:
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Number of overrides removed
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        initial_count = len(self.overrides)
        
        # Remove expired overrides
        self.overrides = [override for override in self.overrides if override.is_active(current_time)]
        
        removed_count = initial_count - len(self.overrides)
        return removed_count

    def get_override_status(self, channel_id: int, current_time: Optional[datetime] = None) -> Dict:
        """
        Get override status for a specific channel.
        
        Args:
            channel_id: Channel ID
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Dictionary containing override status information
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        channel_overrides = self.get_channel_overrides(channel_id, current_time)
        
        if not channel_overrides:
            return {
                "has_override": False,
                "override_intensity": None,
                "override_type": None,
                "override_reason": None,
                "override_priority": None,
            }
        
        # Get the highest priority override
        highest_priority_override = max(channel_overrides, key=lambda x: x.priority)
        
        return {
            "has_override": True,
            "override_intensity": highest_priority_override.get_override_intensity(current_time),
            "override_type": highest_priority_override.override_type,
            "override_reason": highest_priority_override.reason,
            "override_priority": highest_priority_override.priority,
            "override_id": highest_priority_override.override_id,
        } 