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
        
        # Validate parameters
        self._validate_parameters()

    def _validate_parameters(self):
        """
        Validate effect parameters based on effect type.
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if self.effect_type == "fade":
            # Validate fade effect parameters
            if "target_intensity" in self.parameters:
                target_intensity = self.parameters["target_intensity"]
                if not isinstance(target_intensity, (int, float)):
                    raise ValueError("Fade effect requires a valid numeric 'target_intensity' parameter.")
                if not (0.0 <= target_intensity <= 1.0):
                    raise ValueError("Fade effect 'target_intensity' must be between 0.0 and 1.0.")
                    
            if "fade_type" in self.parameters:
                fade_type = self.parameters["fade_type"]
                if not isinstance(fade_type, str):
                    raise ValueError("Fade effect 'fade_type' must be a string.")
                if fade_type not in ["linear", "smooth", "exponential"]:
                    raise ValueError("Fade effect 'fade_type' must be one of: linear, smooth, exponential.")
                    
        elif self.effect_type == "pulse":
            # Validate pulse effect parameters
            if "pulse_frequency" not in self.parameters or not isinstance(self.parameters["pulse_frequency"], (int, float)):
                raise ValueError("Pulse effect requires a valid 'pulse_frequency' parameter.")
            if self.parameters["pulse_frequency"] <= 0:
                raise ValueError("Pulse effect 'pulse_frequency' must be greater than 0.")
                
            if "pulse_amplitude" not in self.parameters or not isinstance(self.parameters["pulse_amplitude"], (int, float)):
                raise ValueError("Pulse effect requires a valid 'pulse_amplitude' parameter.")
            if not (0.0 <= self.parameters["pulse_amplitude"] <= 1.0):
                raise ValueError("Pulse effect 'pulse_amplitude' must be between 0.0 and 1.0.")
                
            if "pulse_phase" in self.parameters:
                pulse_phase = self.parameters["pulse_phase"]
                if not isinstance(pulse_phase, (int, float)):
                    raise ValueError("Pulse effect 'pulse_phase' must be a number.")
                    
        elif self.effect_type == "storm":
            # Validate storm effect parameters
            if "intensity_variation" in self.parameters:
                intensity_variation = self.parameters["intensity_variation"]
                if not isinstance(intensity_variation, (int, float)):
                    raise ValueError("Storm effect 'intensity_variation' must be a number.")
                if not (0.0 <= intensity_variation <= 1.0):
                    raise ValueError("Storm effect 'intensity_variation' must be between 0.0 and 1.0.")
                    
            if "frequency" in self.parameters:
                frequency = self.parameters["frequency"]
                if not isinstance(frequency, (int, float)):
                    raise ValueError("Storm effect 'frequency' must be a number.")
                if frequency <= 0:
                    raise ValueError("Storm effect 'frequency' must be greater than 0.")
                    
            if "storm_intensity" in self.parameters:
                storm_intensity = self.parameters["storm_intensity"]
                if not isinstance(storm_intensity, (int, float)):
                    raise ValueError("Storm effect 'storm_intensity' must be a number.")
                if not (0.0 <= storm_intensity <= 1.0):
                    raise ValueError("Storm effect 'storm_intensity' must be between 0.0 and 1.0.")
                    
        elif self.effect_type == "dim":
            # Validate dim effect parameters
            if "dim_factor" in self.parameters:
                dim_factor = self.parameters["dim_factor"]
                if not isinstance(dim_factor, (int, float)):
                    raise ValueError("Dim effect 'dim_factor' must be a number.")
                if not (0.0 <= dim_factor <= 1.0):
                    raise ValueError("Dim effect 'dim_factor' must be between 0.0 and 1.0.")
                    
        elif self.effect_type == "boost":
            # Validate boost effect parameters
            if "boost_factor" in self.parameters:
                boost_factor = self.parameters["boost_factor"]
                if not isinstance(boost_factor, (int, float)):
                    raise ValueError("Boost effect 'boost_factor' must be a number.")
                if not (0.0 <= boost_factor <= 1.0):
                    raise ValueError("Boost effect 'boost_factor' must be between 0.0 and 1.0.")
                    
        else:
            # Unknown effect type
            raise ValueError(f"Unknown effect type: {self.effect_type}. Supported types: fade, pulse, storm, dim, boost.")

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
    
    This class manages a queue of effects that modify base behavior intensities.
    Effects are processed in priority order and can overlap in time.
    """

    def __init__(self):
        """Initialize the effect queue."""
        self.effects: List[EffectEntry] = []
        self.next_effect_id = 1

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
            current_time: Current time for conflict checking
            
        Returns:
            Effect ID
            
        Raises:
            ValueError: If there's a channel conflict with existing effects
        """
        if start_time is None:
            start_time = datetime.utcnow()
            
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Check for channel conflicts with existing active effects
        active_effects = self.get_active_effects(current_time)
        for active_effect in active_effects:
            # Check if any channels overlap
            overlapping_channels = set(channels) & set(active_effect.channels)
            if overlapping_channels:
                raise ValueError(
                    f"Channel conflict: channels {list(overlapping_channels)} are already "
                    f"part of active effect {active_effect.effect_id} ({active_effect.effect_type})"
                )
        
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
        return effect_id

    def remove_effect(self, effect_id: str) -> bool:
        """
        Remove an effect from the queue.
        
        Args:
            effect_id: ID of effect to remove
            
        Returns:
            True if effect was removed, False if not found
        """
        for i, effect in enumerate(self.effects):
            if effect.effect_id == effect_id:
                del self.effects[i]
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
            
        return [effect for effect in self.effects if effect.is_active(current_time)]

    def get_channel_effects(
        self, channel_id: int, current_time: Optional[datetime] = None
    ) -> List[EffectEntry]:
        """
        Get all effects affecting a specific channel.
        
        Args:
            channel_id: Channel ID
            current_time: Current UTC time (defaults to now)
            
        Returns:
            List of effects affecting the channel
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        return [
            effect for effect in self.effects 
            if channel_id in effect.channels and effect.is_active(current_time)
        ]

    def apply_effects(
        self, base_intensities: Dict[int, float], current_time: Optional[datetime] = None
    ) -> Dict[int, float]:
        """
        Apply all active effects to base intensities.
        
        Args:
            base_intensities: Base intensity values per channel
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Modified intensity values with effects applied
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Start with base intensities
        result_intensities = base_intensities.copy()
        
        # Get active effects sorted by priority (highest first)
        active_effects = sorted(
            self.get_active_effects(current_time),
            key=lambda x: x.priority,
            reverse=True
        )
        
        # Apply each effect to its channels
        for effect in active_effects:
            modified_intensity = effect.calculate_intensity_modification(
                base_intensity=0.0,  # Effects modify the current result, not base
                current_time=current_time
            )
            
            # Apply effect to all affected channels
            for channel_id in effect.channels:
                if channel_id in result_intensities:
                    # Get the current intensity for this channel
                    current_intensity = result_intensities[channel_id]
                    
                    # Apply effect modification
                    if effect.effect_type == "fade":
                        # Fade effect replaces the intensity
                        result_intensities[channel_id] = modified_intensity
                    elif effect.effect_type == "pulse":
                        # Pulse effect modulates the current intensity
                        result_intensities[channel_id] = current_intensity * modified_intensity
                    elif effect.effect_type == "storm":
                        # Storm effect adds variation to current intensity
                        result_intensities[channel_id] = max(0.0, min(1.0, current_intensity + modified_intensity))
                    elif effect.effect_type == "dim":
                        # Dim effect reduces the current intensity
                        result_intensities[channel_id] = current_intensity * (1.0 - modified_intensity)
                    elif effect.effect_type == "boost":
                        # Boost effect increases the current intensity
                        result_intensities[channel_id] = min(1.0, current_intensity + modified_intensity)
                    else:
                        # Default: replace intensity
                        result_intensities[channel_id] = modified_intensity
                        
                    # Ensure intensity stays within bounds
                    result_intensities[channel_id] = max(0.0, min(1.0, result_intensities[channel_id]))
        
        return result_intensities

    def cleanup_expired_effects(self, current_time: Optional[datetime] = None) -> int:
        """
        Remove expired effects from the queue.
        
        Args:
            current_time: Current UTC time (defaults to now)
            
        Returns:
            Number of effects removed
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        initial_count = len(self.effects)
        
        # Remove expired effects
        self.effects = [effect for effect in self.effects if effect.is_active(current_time)]
        
        removed_count = initial_count - len(self.effects)
        return removed_count 