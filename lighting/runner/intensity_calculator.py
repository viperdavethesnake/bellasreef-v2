"""
Intensity calculator for lighting behaviors.

This module provides profile functions for each behavior type that return
the target intensity for a given time, using the behavior's configuration.
"""
import math
import httpx
from datetime import datetime, time
from typing import Any, Dict, Optional
from astral.sun import sun
from astral.moon import phase
from astral import Observer
from datetime import timezone
import logging

from lighting.models.schemas import LightingBehavior, LightingBehaviorType
from shared.core.config import settings

logger = logging.getLogger(__name__)

class IntensityCalculator:
    """
    Calculator for computing lighting behavior intensities.
    
    This class provides profile functions for each behavior type that
    calculate the target intensity based on the current time and behavior
    configuration.
    
    TODO: Add weather influence calculations
    TODO: Add acclimation period calculations
    TODO: Add location-based calculations
    TODO: Add lunar phase calculations
    TODO: Add circadian rhythm calculations
    TODO: Add performance optimization and caching
    """

    def __init__(self):
        """Initialize the intensity calculator."""
        # Initialize HTTP client for weather API calls
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        # Initialize weather cache
        self.weather_cache = {}
        self.weather_cache_expiry_seconds = 600  # Cache weather for 10 minutes
        
        # TODO: Initialize weather service integration
        # TODO: Initialize location service integration
        # TODO: Initialize lunar phase calculator
        # TODO: Initialize caching system

    async def calculate_behavior_intensity(
        self, behavior: LightingBehavior, assignment: Any, current_time: datetime, channel_id: Optional[int] = None
    ) -> float:
        """
        Calculate the target intensity for a behavior at the given time.
        
        Args:
            behavior: The lighting behavior to calculate for
            assignment: The behavior assignment containing start_time for acclimation
            current_time: Current UTC time
            channel_id: Specific channel ID for multi-channel behaviors
            
        Returns:
            Target intensity value (0.0-1.0)
            
        TODO: Add validation for behavior configuration
        TODO: Add error handling for invalid configurations
        TODO: Add performance monitoring
        """
        if not behavior.enabled:
            return 0.0
            
        # Initialize acclimation scale factor
        acclimation_scale = 1.0
        
        # Apply acclimation period if configured
        if behavior.acclimation_days and behavior.acclimation_days > 0:
            # Calculate days elapsed since assignment started
            if hasattr(assignment, 'start_time') and assignment.start_time:
                days_elapsed = (current_time - assignment.start_time).days
                
                # If still within acclimation period, calculate scale factor
                if days_elapsed < behavior.acclimation_days:
                    acclimation_scale = min(1.0, (days_elapsed + 1) / behavior.acclimation_days)
        
        # Calculate base intensity based on behavior type
        base_intensity = await self._calculate_base_intensity(behavior, current_time, channel_id)
        
        # Apply weather influence if enabled
        weather_factor = 1.0
        if hasattr(behavior, 'weather_influence_enabled') and behavior.weather_influence_enabled:
            # Get location from behavior config for weather lookup
            config = behavior.behavior_config or {}
            latitude = config.get("latitude", 0.0)
            longitude = config.get("longitude", 0.0)
            
            if latitude != 0.0 and longitude != 0.0:
                weather_factor = await self._get_weather_factor(latitude, longitude)
        
        # Apply all factors: base intensity * weather factor * acclimation scale
        final_intensity = base_intensity * weather_factor * acclimation_scale
        
        return max(0.0, min(1.0, final_intensity))  # Clamp to valid range

    async def calculate_intensity(
        self, behavior: LightingBehavior, assignment: Any, current_time: datetime, channel_id: Optional[int] = None
    ) -> float:
        """
        Alias for calculate_behavior_intensity for backward compatibility.
        
        Args:
            behavior: The lighting behavior to calculate for
            assignment: The behavior assignment containing start_time for acclimation
            current_time: Current UTC time
            channel_id: Specific channel ID for multi-channel behaviors
            
        Returns:
            Target intensity value (0.0-1.0)
        """
        return await self.calculate_behavior_intensity(behavior, assignment, current_time, channel_id)

    async def _calculate_base_intensity(
        self, behavior: LightingBehavior, current_time: datetime, channel_id: Optional[int] = None
    ) -> float:
        """
        Calculate base intensity for a behavior type.
        
        Args:
            behavior: The lighting behavior
            current_time: Current UTC time
            channel_id: Specific channel ID for multi-channel behaviors
            
        Returns:
            Base intensity value (0.0-1.0)
        """
        behavior_type = behavior.behavior_type
        config = behavior.behavior_config or {}
        
        if behavior_type == LightingBehaviorType.FIXED:
            return self._calculate_fixed_intensity(config)
        elif behavior_type == LightingBehaviorType.DIURNAL:
            return self._calculate_diurnal_intensity(config, current_time, channel_id)
        elif behavior_type == LightingBehaviorType.LUNAR:
            return await self._calculate_lunar_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.MOONLIGHT:
            return await self._calculate_moonlight_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.CIRCADIAN:
            return self._calculate_circadian_intensity(config, current_time, channel_id)
        elif behavior_type == LightingBehaviorType.LOCATION_BASED:
            return await self._calculate_location_based_intensity(config, current_time, channel_id)
        elif behavior_type == LightingBehaviorType.OVERRIDE:
            return self._calculate_override_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.EFFECT:
            return self._calculate_effect_intensity(config, current_time)
        else:
            logger.error(f"Unknown behavior type: {behavior_type}")
            return 0.0

    def _calculate_fixed_intensity(self, config: Dict[str, Any]) -> float:
        """
        Calculate intensity for Fixed behavior type.
        
        Args:
            config: Behavior configuration
            
        Returns:
            Fixed intensity value (0.0-1.0)
        """
        try:
            intensity = config.get("intensity", 0.5)
            
            # Validate intensity is a number and within bounds
            if not isinstance(intensity, (int, float)):
                logger.error(f"Invalid 'intensity' for fixed behavior: {intensity} (not a number)")
                return 0.0
                
            if intensity < 0.0 or intensity > 1.0:
                logger.error(f"Invalid 'intensity' for fixed behavior: {intensity} (must be 0.0-1.0)")
                return 0.0
                
            return float(intensity)
            
        except Exception as e:
            logger.error(f"Error in fixed intensity calculation: {e}")
            return 0.0

    def _calculate_diurnal_intensity(
        self, config: Dict[str, Any], current_time: datetime, channel_id: Optional[int] = None
    ) -> float:
        """
        Calculate intensity for Diurnal behavior type.
        
        Args:
            config: Behavior configuration with timing and channels
            current_time: Current UTC time
            channel_id: Specific channel ID to look up peak_intensity
            
        Returns:
            Diurnal intensity value (0.0-1.0)
        """
        try:
            # Parse timing configuration
            timing = config.get("timing", {})
            if not timing:
                logger.error("Missing 'timing' configuration for diurnal behavior")
                return 0.0
            
            # Parse time strings to time objects
            sunrise_start = self._parse_time_string(timing.get("sunrise_start", "08:00"))
            sunrise_end = self._parse_time_string(timing.get("sunrise_end", "10:00"))
            peak_start = self._parse_time_string(timing.get("peak_start", "10:00"))
            peak_end = self._parse_time_string(timing.get("peak_end", "18:00"))
            sunset_start = self._parse_time_string(timing.get("sunset_start", "18:00"))
            sunset_end = self._parse_time_string(timing.get("sunset_end", "20:00"))
            
            # Get channel-specific peak intensity
            channels = config.get("channels", [])
            peak_intensity = 1.0  # Default peak intensity
            
            if channel_id is not None and channels:
                # Find the specific channel configuration
                channel_config = next((ch for ch in channels if ch.get("channel_id") == channel_id), None)
                if channel_config:
                    peak_intensity = channel_config.get("peak_intensity", 1.0)
                    if not isinstance(peak_intensity, (int, float)) or peak_intensity < 0.0 or peak_intensity > 1.0:
                        logger.error(f"Invalid peak_intensity for channel {channel_id}: {peak_intensity}")
                        peak_intensity = 1.0
            
            # Get ramp curve type
            ramp_curve = config.get("ramp_curve", "linear")
            
            # Get current time as time object
            current_time_obj = current_time.time()
            
            # Determine current phase and calculate intensity
            if sunrise_start <= current_time_obj <= sunrise_end:
                # Sunrise phase
                progress = self._calculate_progress(current_time_obj, sunrise_start, sunrise_end)
                if ramp_curve == "exponential":
                    progress = self._apply_exponential_ramp(progress)
                return peak_intensity * progress
                
            elif peak_start <= current_time_obj <= peak_end:
                # Peak phase
                return peak_intensity
                
            elif sunset_start <= current_time_obj <= sunset_end:
                # Sunset phase
                progress = self._calculate_progress(current_time_obj, sunset_start, sunset_end)
                if ramp_curve == "exponential":
                    progress = self._apply_exponential_ramp(progress)
                return peak_intensity * (1.0 - progress)
                
            else:
                # Dark phase
                return 0.0
                
        except Exception as e:
            logger.error(f"Error in diurnal intensity calculation: {e}")
            return 0.0

    async def _calculate_lunar_intensity(
        self, config: Dict[str, Any], current_time: datetime
    ) -> float:
        """
        Calculate intensity for Lunar behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            
        Returns:
            Lunar intensity value (0.0-1.0)
        """
        try:
            # Parse configuration
            mode = config.get("mode", "true")
            max_intensity = config.get("max_intensity", 0.3)
            
            # Validate max_intensity
            if not isinstance(max_intensity, (int, float)) or max_intensity < 0.0 or max_intensity > 1.0:
                logger.error(f"Invalid max_intensity for lunar behavior: {max_intensity}")
                return 0.0
            
            # Calculate lunar phase (0.0 = new moon, 1.0 = full moon)
            lunar_phase = self._calculate_lunar_phase(current_time)
            
            # Calculate base intensity
            base_intensity = max_intensity * lunar_phase
            
            if mode == "scheduled":
                # Check if within scheduled time window
                start_time = self._parse_time_string(config.get("start_time", "21:00"))
                end_time = self._parse_time_string(config.get("end_time", "06:00"))
                
                current_time_obj = current_time.time()
                if self._is_time_in_window(current_time_obj, start_time, end_time):
                    return base_intensity
                else:
                    return 0.0
                    
            elif mode == "true":
                # Check if moon is above horizon (simplified - assume moon is up during night)
                current_hour = current_time.hour + current_time.minute / 60.0
                if 18.0 <= current_hour or current_hour <= 6.0:  # Night hours
                    return base_intensity
                else:
                    return 0.0
            else:
                logger.error(f"Unknown lunar mode: {mode}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error in lunar intensity calculation: {e}")
            return 0.0

    async def _calculate_moonlight_intensity(
        self, config: Dict[str, Any], current_time: datetime
    ) -> float:
        """
        Calculate intensity for Moonlight behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            
        Returns:
            Moonlight intensity value (0.0-1.0)
        """
        try:
            # Parse configuration
            intensity = config.get("intensity", 0.05)
            start_time = self._parse_time_string(config.get("start_time", "20:00"))
            end_time = self._parse_time_string(config.get("end_time", "08:00"))
            
            # Validate intensity
            if not isinstance(intensity, (int, float)) or intensity < 0.0 or intensity > 1.0:
                logger.error(f"Invalid intensity for moonlight behavior: {intensity}")
                return 0.0
            
            # Check if current time is within moonlight period
            current_time_obj = current_time.time()
            if self._is_time_in_window(current_time_obj, start_time, end_time):
                return intensity
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error in moonlight intensity calculation: {e}")
            return 0.0

    def _calculate_circadian_intensity(
        self, config: Dict[str, Any], current_time: datetime, channel_id: Optional[int] = None
    ) -> float:
        """
        Calculate intensity for 24-Hour Circadian behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            channel_id: Specific channel ID for multi-channel behaviors
            
        Returns:
            Circadian intensity value (0.0-1.0)
        """
        try:
            # This is a composite behavior that combines diurnal and lunar/moonlight
            # Check if we're in day or night phase
            current_hour = current_time.hour + current_time.minute / 60.0
            
            # Simple day/night determination (6:00-18:00 = day)
            if 6.0 <= current_hour <= 18.0:
                # Day phase - use diurnal logic
                return self._calculate_diurnal_intensity(config, current_time, channel_id)
            else:
                # Night phase - use lunar or moonlight logic
                if "lunar_config" in config:
                    return await self._calculate_lunar_intensity(config["lunar_config"], current_time)
                elif "moonlight_config" in config:
                    return await self._calculate_moonlight_intensity(config["moonlight_config"], current_time)
                else:
                    # Default to very low moonlight
                    return 0.05
                    
        except Exception as e:
            logger.error(f"Error in circadian intensity calculation: {e}")
            return 0.0

    async def _calculate_location_based_intensity(
        self, config: Dict[str, Any], current_time: datetime, channel_id: Optional[int] = None
    ) -> float:
        """
        Calculate intensity for Location-Based behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            channel_id: Specific channel ID for multi-channel behaviors
            
        Returns:
            Location-based intensity value (0.0-1.0)
        """
        try:
            # Parse location configuration
            latitude = config.get("latitude", 0.0)
            longitude = config.get("longitude", 0.0)
            time_offset = config.get("time_offset", {})
            
            # Validate coordinates
            if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
                logger.error(f"Invalid coordinates for location-based behavior: lat={latitude}, lon={longitude}")
                return 0.0
            
            if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
                logger.error(f"Coordinates out of range: lat={latitude}, lon={longitude}")
                return 0.0
            
            # Apply time offset if specified
            adjusted_time = current_time
            if time_offset:
                offset_hours = time_offset.get("hours", 0)
                offset_minutes = time_offset.get("minutes", 0)
                if offset_hours or offset_minutes:
                    from datetime import timedelta
                    adjusted_time = current_time + timedelta(hours=offset_hours, minutes=offset_minutes)
            
            # Create observer for astronomical calculations
            observer = Observer(latitude=latitude, longitude=longitude)
            
            # Get solar events for the current date
            solar_events = sun(observer.observer, date=adjusted_time.date(), tzinfo=timezone.utc)
            
            # Check if sun is up
            sunrise = solar_events['sunrise']
            sunset = solar_events['sunset']
            
            if sunrise <= adjusted_time <= sunset:
                # Sun is up - use diurnal logic with calculated times
                diurnal_config = {
                    "timing": {
                        "sunrise_start": sunrise.strftime("%H:%M"),
                        "sunrise_end": (sunrise + timedelta(hours=2)).strftime("%H:%M"),
                        "peak_start": (sunrise + timedelta(hours=2)).strftime("%H:%M"),
                        "peak_end": (sunset - timedelta(hours=2)).strftime("%H:%M"),
                        "sunset_start": (sunset - timedelta(hours=2)).strftime("%H:%M"),
                        "sunset_end": sunset.strftime("%H:%M")
                    },
                    "channels": config.get("channels", []),
                    "ramp_curve": config.get("ramp_curve", "linear")
                }
                return self._calculate_diurnal_intensity(diurnal_config, adjusted_time, channel_id)
            else:
                # Sun is down - check if moon is up
                lunar_phase = self._calculate_lunar_phase(adjusted_time)
                if lunar_phase > 0.1:  # Moon is visible
                    lunar_config = {
                        "mode": "true",
                        "max_intensity": config.get("moonlight_intensity", 0.1)
                    }
                    return await self._calculate_lunar_intensity(lunar_config, adjusted_time)
                else:
                    return 0.0
                    
        except Exception as e:
            logger.error(f"Error in location-based intensity calculation: {e}")
            return 0.0

    def _calculate_override_intensity(
        self, config: Dict[str, Any], current_time: datetime
    ) -> float:
        """
        Calculate intensity for Override behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            
        Returns:
            Override intensity value (0.0-1.0)
        """
        try:
            # Parse configuration
            intensity = config.get("intensity", 0.5)
            start_time = config.get("start_time")
            end_time = config.get("end_time")
            
            # Validate intensity
            if not isinstance(intensity, (int, float)) or intensity < 0.0 or intensity > 1.0:
                logger.error(f"Invalid intensity for override behavior: {intensity}")
                return 0.0
            
            # Check time constraints if specified
            if start_time and end_time:
                if isinstance(start_time, str):
                    start_time = self._parse_time_string(start_time)
                if isinstance(end_time, str):
                    end_time = self._parse_time_string(end_time)
                
                current_time_obj = current_time.time()
                if not self._is_time_in_window(current_time_obj, start_time, end_time):
                    return 0.0
            
            return intensity
            
        except Exception as e:
            logger.error(f"Error in override intensity calculation: {e}")
            return 0.0

    def _calculate_effect_intensity(
        self, config: Dict[str, Any], current_time: datetime
    ) -> float:
        """
        Calculate intensity for Effect behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            
        Returns:
            Effect intensity value (0.0-1.0)
        """
        try:
            effect_type = config.get("effect_type", "fade")
            effect_parameters = config.get("effect_parameters", {})
            
            if effect_type == "fade":
                return self._calculate_fade_effect(effect_parameters, current_time)
            elif effect_type == "pulse":
                return self._calculate_pulse_effect(effect_parameters, current_time)
            elif effect_type == "storm":
                return self._calculate_storm_effect(effect_parameters, current_time)
            else:
                logger.error(f"Unknown effect type: {effect_type}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error in effect intensity calculation: {e}")
            return 0.0

    # Helper methods

    def _parse_time_string(self, time_str: str) -> time:
        """Parse time string in HH:MM format to time object."""
        try:
            if isinstance(time_str, time):
                return time_str
            if isinstance(time_str, str):
                hour, minute = map(int, time_str.split(':'))
                return time(hour, minute)
            else:
                logger.error(f"Invalid time format: {time_str}")
                return time(12, 0)  # Default to noon
        except Exception as e:
            logger.error(f"Error parsing time string '{time_str}': {e}")
            return time(12, 0)

    def _calculate_progress(self, current: time, start: time, end: time) -> float:
        """Calculate progress (0.0-1.0) between start and end times."""
        try:
            current_seconds = current.hour * 3600 + current.minute * 60
            start_seconds = start.hour * 3600 + start.minute * 60
            end_seconds = end.hour * 3600 + end.minute * 60
            
            if end_seconds < start_seconds:  # Overnight period
                end_seconds += 24 * 3600
                if current_seconds < start_seconds:
                    current_seconds += 24 * 3600
            
            total_duration = end_seconds - start_seconds
            elapsed = current_seconds - start_seconds
            
            if total_duration <= 0:
                return 0.0
            
            progress = elapsed / total_duration
            return max(0.0, min(1.0, progress))
            
        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            return 0.0

    def _apply_exponential_ramp(self, progress: float) -> float:
        """Apply exponential easing to ramp progress."""
        return progress * progress * (3.0 - 2.0 * progress)  # Smoothstep function

    def _is_time_in_window(self, current: time, start: time, end: time) -> bool:
        """Check if current time is within the specified window."""
        try:
            current_seconds = current.hour * 3600 + current.minute * 60
            start_seconds = start.hour * 3600 + start.minute * 60
            end_seconds = end.hour * 3600 + end.minute * 60
            
            if end_seconds < start_seconds:  # Overnight period
                return current_seconds >= start_seconds or current_seconds <= end_seconds
            else:
                return start_seconds <= current_seconds <= end_seconds
                
        except Exception as e:
            logger.error(f"Error checking time window: {e}")
            return False

    def _calculate_lunar_phase(self, current_time: datetime) -> float:
        """Calculate lunar phase (0.0 = new moon, 1.0 = full moon)."""
        try:
            # Get lunar phase from astral library
            lunar_phase = phase(current_time.date())
            
            # Convert to 0.0-1.0 scale where 0.0 = new moon, 1.0 = full moon
            # astral returns 0-29.5, where 0 = new moon, 14.75 = full moon
            normalized_phase = lunar_phase / 29.5
            
            # Convert to sine wave for smooth transitions
            return (math.sin(normalized_phase * 2 * math.pi) + 1) / 2
            
        except Exception as e:
            logger.error(f"Error calculating lunar phase: {e}")
            return 0.5  # Default to half moon

    async def _get_weather_factor(self, latitude: float, longitude: float) -> float:
        """
        Get weather influence factor (0.0-1.0) from OpenWeatherMap API.
        
        Args:
            latitude: Location latitude in degrees
            longitude: Location longitude in degrees
            
        Returns:
            Weather factor (0.0-1.0) where 1.0 = clear skies, 0.3 = heavy clouds
        """
        # Create cache key for this location
        cache_key = f"{latitude:.3f},{longitude:.3f}"
        current_time = datetime.now()
        
        # Check cache first
        if cache_key in self.weather_cache:
            cached_data = self.weather_cache[cache_key]
            cache_age = (current_time - cached_data['timestamp']).total_seconds()
            
            if cache_age < self.weather_cache_expiry_seconds:
                return cached_data['factor']
        
        # Check if API key is configured
        api_key = getattr(settings, 'LIGHTING_WEATHER_API_KEY', None)
        if not api_key or api_key == "changeme":
            logger.warning("Weather API key not configured. Weather influence disabled.")
            return 1.0  # No weather effect
        
        try:
            # Make API call to OpenWeatherMap
            url = "https://api.openweathermap.org/data/3.0/onecall"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': api_key,
                'exclude': 'minutely,hourly,daily,alerts'
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            cloud_percentage = data['current']['clouds']
            
            # Convert cloud percentage (0-100) to intensity multiplier (1.0-0.3)
            # 0% clouds = 1.0 multiplier (clear skies)
            # 100% clouds = 0.3 multiplier (heavy cloud cover)
            multiplier = 1.0 - (cloud_percentage / 100.0) * 0.7
            
            # Cache the result
            self.weather_cache[cache_key] = {
                'factor': multiplier,
                'timestamp': current_time
            }
            
            return multiplier
            
        except Exception as e:
            logger.error(f"Weather API call failed: {e}")
            return 1.0  # Default to no weather effect on failure

    def _calculate_fade_effect(self, parameters: Dict[str, Any], current_time: datetime) -> float:
        """Calculate fade effect intensity."""
        target_intensity = parameters.get("target_intensity", 0.8)
        fade_duration = parameters.get("fade_duration", 10)  # minutes
        
        # Simplified fade calculation
        return max(0.0, min(1.0, target_intensity))

    def _calculate_pulse_effect(self, parameters: Dict[str, Any], current_time: datetime) -> float:
        """Calculate pulse effect intensity."""
        base_intensity = parameters.get("base_intensity", 0.5)
        pulse_frequency = parameters.get("pulse_frequency", 1.0)  # Hz
        pulse_amplitude = parameters.get("pulse_amplitude", 0.3)
        
        # Calculate pulse based on time
        seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        pulse_value = math.sin(2 * math.pi * pulse_frequency * seconds)
        
        return max(0.0, min(1.0, base_intensity + pulse_amplitude * pulse_value))

    def _calculate_storm_effect(self, parameters: Dict[str, Any], current_time: datetime) -> float:
        """Calculate storm effect intensity."""
        base_intensity = parameters.get("base_intensity", 0.3)
        intensity_variation = parameters.get("intensity_variation", 0.2)
        frequency = parameters.get("frequency", 0.1)  # Hz
        
        # Calculate storm variation based on time
        seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        variation = math.sin(2 * math.pi * frequency * seconds) * intensity_variation
        
        return max(0.0, min(1.0, base_intensity + variation))

# Create a single instance of the service
intensity_calculator = IntensityCalculator() 