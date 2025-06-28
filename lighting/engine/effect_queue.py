"""
Effect queue for lighting behaviors.

This module provides the effect queue system for managing temporary
lighting effects that modify base behavior intensities.
"""
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from lighting.models.schemas import LightingBehaviorType


class EffectEntry:
    """
    Represents an effect in the effect queue.
    
    TODO: Add effect validation
    TODO: Add effect priority system
    TODO: Add effect conflict resolution
    TODO: Add effect cleanup logic
    """

    def __init__(
        self,
        effect_id: str,
        effect_type: str,
        channels: List[int],
        parameters: Dict[str, Any],
        start_time: datetime,
        duration_minutes: int,
        priority: int = 1,
    ):
        """
        Initialize an effect entry.
        
        Args:
            effect_id: Unique effect identifier
            effect_type: Type of effect (fade, pulse, storm, etc.)
            channels: List of channel IDs affected
            parameters: Effect-specific parameters
            start_time: When the effect should start (UTC)
            duration_minutes: How long the effect should last
            priority: Effect priority (higher = more important)
        """
        self.effect_id = effect_id
        self.effect_type = effect_type
        self.channels = channels
        self.parameters = parameters
        self.start_time = start_time
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.created_at = datetime.utcnow()
        
        # TODO: Add effect validation
        # TODO: Add parameter validation
        # TODO: Add channel validation

    def is_active(self, current_time: datetime) -> bool:
        """
        Check if the effect is currently active.
        
        Args:
            current_time: Current UTC time
            
        Returns:
            True if effect is active
        """
        end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        return self.start_time <= current_time <= end_time

    def get_progress(self, current_time: datetime) -> float:
        """
        Get the progress of the effect (0.0-1.0).
        
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

    def calculate_intensity_modification(self, base_intensity: float, current_time: datetime) -> float:
        """
        Calculate how this effect modifies the base intensity.
        
        Args:
            base_intensity: Base intensity value (0.0-1.0)
            current_time: Current UTC time
            
        Returns:
            Modified intensity value (0.0-1.0)
        """
        if not self.is_active(current_time):
            return base_intensity
            
        progress = self.get_progress(current_time)
        
        if self.effect_type == "fade":
            return self._apply_fade_effect(base_intensity, progress)
        elif self.effect_type == "pulse":
            return self._apply_pulse_effect(base_intensity, current_time)
        elif self.effect_type == "storm":
            return self._apply_storm_effect(base_intensity, current_time)
        elif self.effect_type == "dim":
            return self._apply_dim_effect(base_intensity, progress)
        elif self.effect_type == "boost":
            return self._apply_boost_effect(base_intensity, progress)
        else:
            return base_intensity

    def _apply_fade_effect(self, base_intensity: float, progress: float) -> float:
        """Apply fade effect to base intensity."""
        target_intensity = self.parameters.get("target_intensity", 0.8)
        fade_type = self.parameters.get("fade_type", "linear")  # linear, smooth, exponential
        
        if fade_type == "smooth":
            # Use smoothstep function
            smooth_progress = 3 * progress * progress - 2 * progress * progress * progress
            return base_intensity + (target_intensity - base_intensity) * smooth_progress
        elif fade_type == "exponential":
            # Use exponential curve
            exp_progress = math.pow(progress, 2)
            return base_intensity + (target_intensity - base_intensity) * exp_progress
        else:
            # Linear fade
            return base_intensity + (target_intensity - base_intensity) * progress

    def _apply_pulse_effect(self, base_intensity: float, current_time: datetime) -> float:
        """Apply pulse effect to base intensity."""
        pulse_frequency = self.parameters.get("pulse_frequency", 1.0)  # Hz
        pulse_amplitude = self.parameters.get("pulse_amplitude", 0.3)
        pulse_phase = self.parameters.get("pulse_phase", 0.0)  # radians
        
        # Calculate pulse value
        seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        pulse_value = math.sin(2 * math.pi * pulse_frequency * seconds + pulse_phase)
        
        # Apply pulse to base intensity
        modification = pulse_amplitude * pulse_value
        return max(0.0, min(1.0, base_intensity + modification))

    def _apply_storm_effect(self, base_intensity: float, current_time: datetime) -> float:
        """Apply storm effect to base intensity."""
        intensity_variation = self.parameters.get("intensity_variation", 0.2)
        frequency = self.parameters.get("frequency", 0.1)  # Hz
        storm_intensity = self.parameters.get("storm_intensity", 0.3)
        
        # Calculate storm variation
        seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        variation = math.sin(2 * math.pi * frequency * seconds) * intensity_variation
        
        # Apply storm effect
        storm_value = storm_intensity + variation
        return max(0.0, min(1.0, base_intensity * storm_value))

    def _apply_dim_effect(self, base_intensity: float, progress: float) -> float:
        """Apply dimming effect to base intensity."""
        dim_factor = self.parameters.get("dim_factor", 0.5)
        return base_intensity * (1.0 - dim_factor * progress)

    def _apply_boost_effect(self, base_intensity: float, progress: float) -> float:
        """Apply boost effect to base intensity."""
        boost_factor = self.parameters.get("boost_factor", 0.3)
        return min(1.0, base_intensity * (1.0 + boost_factor * progress))


class EffectQueue:
    """
    Queue for managing lighting effects.
    
    This class manages a queue of effects that can modify base
    behavior intensities. Effects are processed in priority order
    and can overlap in time.
    
    TODO: Add effect persistence
    TODO: Add effect scheduling
    TODO: Add effect monitoring
    TODO: Add effect cleanup
    """

    def __init__(self):
        """Initialize the effect queue."""
        self.effects: List[EffectEntry] = []
        self.next_effect_id = 1
        
        # TODO: Initialize effect storage
        # TODO: Initialize effect scheduler
        # TODO: Initialize effect monitor

    def add_effect(
        self,
        effect_type: str,
        channels: List[int],
        parameters: Dict[str, Any],
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60,
        priority: int = 1,
        current_time: Optional[datetime] = None,
    ) -> str:
        """
        Add an effect to the queue.
        
        Args:
            effect_type: Type of effect
            channels: List of channel IDs affected
            parameters: Effect-specific parameters
            start_time: When to start (defaults to now)
            duration_minutes: How long to run
            priority: Effect priority
            current_time: Current time for conflict checking (defaults to now)
            
        Returns:
            Effect ID
            
        Raises:
            ValueError: If there are conflicts with already active effects
            
        TODO: Add effect validation
        TODO: Add resource checking
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        if start_time is None:
            start_time = datetime.utcnow()
            
        # Check for conflicts with already active effects
        active_effects = self.get_active_effects(current_time)
        if active_effects:
            busy_channels = {ch for effect in active_effects for ch in effect.channels}
            requested_channels = set(channels)
            if not busy_channels.isdisjoint(requested_channels):
                conflicting_channels = busy_channels.intersection(requested_channels)
                raise ValueError(f"Cannot start effect. Channel(s) {conflicting_channels} are already running an active effect.")
            
        effect_id = f"effect_{self.next_effect_id}"
        self.next_effect_id += 1
        
        effect = EffectEntry(
            effect_id=effect_id,
            effect_type=effect_type,
            channels=channels,
            parameters=parameters,
            start_time=start_time,
            duration_minutes=duration_minutes,
            priority=priority,
        )
        
        self.effects.append(effect)
        
        # Sort by priority and start time
        self.effects.sort(key=lambda x: (-x.priority, x.start_time))
        
        # TODO: Log effect addition
        # TODO: Trigger effect scheduling
        
        return effect_id

    def remove_effect(self, effect_id: str) -> bool:
        """
        Remove an effect from the queue.
        
        Args:
            effect_id: Effect ID to remove
            
        Returns:
            True if effect was removed
        """
        for i, effect in enumerate(self.effects):
            if effect.effect_id == effect_id:
                del self.effects[i]
                # TODO: Add effect cleanup
                # TODO: Log effect removal
                return True
        return False

    def get_active_effects(
        self, current_time: Optional[datetime] = None
    ) -> List[EffectEntry]:
        """
        Get all currently active effects.
        
        Args:
            current_time: Current UTC time (defaults to now)
            
        Returns:
            List of active effects
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        active_effects = [effect for effect in self.effects if effect.is_active(current_time)]
        return active_effects

    def get_channel_effects(
        self, channel_id: int, current_time: Optional[datetime] = None
    ) -> List[EffectEntry]:
        """
        Get active effects for a specific channel.
        
        Args:
            channel_id: Channel ID
            current_time: Current UTC time (defaults to now)
            
        Returns:
            List of active effects for the channel
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        channel_effects = [
            effect for effect in self.effects 
            if effect.is_active(current_time) and channel_id in effect.channels
        ]
        return channel_effects

    def apply_effects(
        self, base_intensities: Dict[int, float], current_time: Optional[datetime] = None
    ) -> Dict[int, float]:
        """
        Apply active effects to base intensities.
        
        Args:
            base_intensities: Base intensity values per channel
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Modified intensity values with effects applied
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Get active effects
        active_effects = self.get_active_effects(current_time)
        
        # Apply effects by priority (higher priority first)
        modified_intensities = base_intensities.copy()
        
        for effect in active_effects:
            for channel_id in effect.channels:
                if channel_id in modified_intensities:
                    base_intensity = modified_intensities[channel_id]
                    modified_intensity = effect.calculate_intensity_modification(
                        base_intensity, current_time
                    )
                    modified_intensities[channel_id] = modified_intensity
        
        return modified_intensities

    def cleanup_expired_effects(self, current_time: Optional[datetime] = None) -> int:
        """
        Remove expired effects from the queue.
        
        Args:
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Number of effects removed
            
        TODO: Implement effect cleanup
        TODO: Add cleanup logging
        TODO: Add cleanup metrics
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Find expired effects
        expired_effects = [
            effect for effect in self.effects 
            if not effect.is_active(current_time)
        ]
        
        # Remove expired effects
        for expired_effect in expired_effects:
            self.effects.remove(expired_effect)
        
        # TODO: Log cleanup actions
        
        return len(expired_effects) 