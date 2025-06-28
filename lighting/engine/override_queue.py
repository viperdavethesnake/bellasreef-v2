"""
Override queue for lighting behaviors.

This module provides the override queue system for managing temporary
lighting overrides that take precedence over base behaviors.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from lighting.models.schemas import LightingBehaviorType


class OverrideEntry:
    """
    Represents an override in the override queue.
    
    TODO: Add override validation
    TODO: Add override priority system
    TODO: Add override conflict resolution
    TODO: Add override cleanup logic
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
            
        Returns:
            Override ID
            
        TODO: Add override validation
        TODO: Add conflict detection
        TODO: Add resource checking
        """
        if start_time is None:
            start_time = datetime.utcnow()
            
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
        )
        
        self.overrides.append(override)
        
        # Sort by priority and start time
        self.overrides.sort(key=lambda x: (-x.priority, x.start_time))
        
        # TODO: Log override addition
        # TODO: Trigger override scheduling
        
        return override_id

    def remove_override(self, override_id: str) -> bool:
        """
        Remove an override from the queue.
        
        Args:
            override_id: Override ID to remove
            
        Returns:
            True if override was removed
        """
        for i, override in enumerate(self.overrides):
            if override.override_id == override_id:
                del self.overrides[i]
                # TODO: Add override cleanup
                # TODO: Log override removal
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
            
        active_overrides = [override for override in self.overrides if override.is_active(current_time)]
        return active_overrides

    def get_channel_overrides(
        self, channel_id: int, current_time: Optional[datetime] = None
    ) -> List[OverrideEntry]:
        """
        Get active overrides for a specific channel.
        
        Args:
            channel_id: Channel ID
            current_time: Current UTC time (defaults to now)
            
        Returns:
            List of active overrides for the channel
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        channel_overrides = [
            override for override in self.overrides 
            if override.is_active(current_time) and channel_id in override.channels
        ]
        return channel_overrides

    def apply_overrides(
        self, intensities: Dict[int, float], current_time: Optional[datetime] = None
    ) -> Dict[int, float]:
        """
        Apply active overrides to intensities.
        
        Args:
            intensities: Current intensity values per channel
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Modified intensity values with overrides applied
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Get active overrides
        active_overrides = self.get_active_overrides(current_time)
        
        # Apply overrides by priority (higher priority first)
        modified_intensities = intensities.copy()
        
        for override in active_overrides:
            for channel_id in override.channels:
                if channel_id in modified_intensities:
                    override_intensity = override.get_override_intensity(current_time)
                    modified_intensities[channel_id] = override_intensity
        
        return modified_intensities

    def cleanup_expired_overrides(self, current_time: Optional[datetime] = None) -> int:
        """
        Remove expired overrides from the queue.
        
        Args:
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Number of overrides removed
            
        TODO: Implement override cleanup
        TODO: Add cleanup logging
        TODO: Add cleanup metrics
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Find expired overrides
        expired_overrides = [
            override for override in self.overrides 
            if not override.is_active(current_time)
        ]
        
        # Remove expired overrides
        for expired_override in expired_overrides:
            self.overrides.remove(expired_override)
        
        # TODO: Log cleanup actions
        
        return len(expired_overrides)

    def get_override_status(self, channel_id: int, current_time: Optional[datetime] = None) -> Dict:
        """
        Get override status for a specific channel.
        
        Args:
            channel_id: Channel ID
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Dictionary containing override status information
            
        TODO: Implement override status reporting
        TODO: Add override history
        TODO: Add override metrics
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Get active overrides for channel
        channel_overrides = self.get_channel_overrides(channel_id, current_time)
        
        if channel_overrides:
            # Get highest priority override
            highest_priority_override = max(channel_overrides, key=lambda x: x.priority)
            
            return {
                "channel_id": channel_id,
                "current_time": current_time,
                "has_override": True,
                "override_type": highest_priority_override.override_type,
                "override_intensity": highest_priority_override.get_override_intensity(current_time),
                "override_priority": highest_priority_override.priority,
                "override_reason": highest_priority_override.reason,
                "override_progress": highest_priority_override.get_progress(current_time),
            }
        else:
            return {
                "channel_id": channel_id,
                "current_time": current_time,
                "has_override": False,
                "override_type": None,
                "override_intensity": 0.0,
                "override_priority": 0,
                "override_reason": None,
                "override_progress": 0.0,
            } 