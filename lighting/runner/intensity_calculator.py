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
        self, behavior: LightingBehavior, current_time: datetime
    ) -> float:
        """
        Calculate the target intensity for a behavior at the given time.
        
        Args:
            behavior: The lighting behavior to calculate for
            current_time: Current UTC time
            
        Returns:
            Target intensity value (0.0-1.0)
            
        TODO: Add validation for behavior configuration
        TODO: Add error handling for invalid configurations
        TODO: Add performance monitoring
        """
        if not behavior.enabled:
            return 0.0
            
        # TODO: Apply acclimation period if configured
        
        # Calculate base intensity based on behavior type
        base_intensity = await self._calculate_base_intensity(behavior, current_time)
        
        # Apply weather influence if enabled
        if hasattr(behavior, 'weather_influence_enabled') and behavior.weather_influence_enabled:
            # Get location from behavior config for weather lookup
            config = behavior.behavior_config or {}
            latitude = config.get("latitude", 0.0)
            longitude = config.get("longitude", 0.0)
            
            if latitude != 0.0 and longitude != 0.0:
                weather_factor = await self._get_weather_factor(latitude, longitude)
                base_intensity *= weather_factor
        
        # TODO: Apply acclimation modifications
        
        return max(0.0, min(1.0, base_intensity))  # Clamp to valid range

    async def _calculate_base_intensity(
        self, behavior: LightingBehavior, current_time: datetime
    ) -> float:
        """
        Calculate base intensity for a behavior type.
        
        Args:
            behavior: The lighting behavior
            current_time: Current UTC time
            
        Returns:
            Base intensity value (0.0-1.0)
        """
        behavior_type = behavior.behavior_type
        config = behavior.behavior_config or {}
        
        if behavior_type == LightingBehaviorType.FIXED:
            return self._calculate_fixed_intensity(config)
        elif behavior_type == LightingBehaviorType.DIURNAL:
            return self._calculate_diurnal_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.LUNAR:
            return await self._calculate_lunar_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.MOONLIGHT:
            return await self._calculate_moonlight_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.CIRCADIAN:
            return self._calculate_circadian_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.LOCATION_BASED:
            return await self._calculate_location_based_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.OVERRIDE:
            return self._calculate_override_intensity(config, current_time)
        elif behavior_type == LightingBehaviorType.EFFECT:
            return self._calculate_effect_intensity(config, current_time)
        else:
            # TODO: Add proper error handling
            return 0.0

    def _calculate_fixed_intensity(self, config: Dict[str, Any]) -> float:
        """
        Calculate intensity for Fixed behavior type.
        
        Args:
            config: Behavior configuration
            
        Returns:
            Fixed intensity value (0.0-1.0)
        """
        intensity = config.get("intensity", 0.5)
        
        # Validate intensity is within bounds
        if not isinstance(intensity, (int, float)) or intensity < 0.0 or intensity > 1.0:
            return 0.5  # Default to 50% if invalid
            
        return float(intensity)

    def _calculate_diurnal_intensity(
        self, config: Dict[str, Any], current_time: datetime
    ) -> float:
        """
        Calculate intensity for Diurnal behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            
        Returns:
            Diurnal intensity value (0.0-1.0)
        """
        # Extract configuration parameters
        sunrise_hour = config.get("sunrise_hour", 6.0)
        sunset_hour = config.get("sunset_hour", 18.0)
        peak_intensity = config.get("peak_intensity", 1.0)
        min_intensity = config.get("min_intensity", 0.0)
        ramp_duration = config.get("ramp_duration", 2.0)  # hours
        
        # Validate parameters
        peak_intensity = max(0.0, min(1.0, peak_intensity))
        min_intensity = max(0.0, min(1.0, min_intensity))
        ramp_duration = max(0.5, min(6.0, ramp_duration))
        
        # Calculate current time in hours
        current_hour = current_time.hour + current_time.minute / 60.0
        
        # Handle day/night cycle
        if sunrise_hour <= current_hour <= sunset_hour:
            # Daytime - calculate peak intensity
            if current_hour <= sunrise_hour + ramp_duration:
                # Sunrise ramp
                progress = (current_hour - sunrise_hour) / ramp_duration
                return min_intensity + (peak_intensity - min_intensity) * self._smooth_ramp(progress)
            elif current_hour >= sunset_hour - ramp_duration:
                # Sunset ramp
                progress = (sunset_hour - current_hour) / ramp_duration
                return min_intensity + (peak_intensity - min_intensity) * self._smooth_ramp(progress)
            else:
                # Peak daylight
                return peak_intensity
        else:
            # Nighttime
            return min_intensity

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
        # Extract configuration parameters
        max_lunar_intensity = config.get("max_lunar_intensity", 0.3)
        weather_influence = config.get("weather_influence", True)
        
        # Validate parameters
        max_lunar_intensity = max(0.0, min(1.0, max_lunar_intensity))
        
        # Calculate lunar phase (simplified - 0.0 = new moon, 1.0 = full moon)
        lunar_phase = self._calculate_lunar_phase(current_time)
        
        # Calculate lunar elevation (simplified - 0.0 = below horizon, 1.0 = zenith)
        lunar_elevation = self._calculate_lunar_elevation(current_time)
        
        # Calculate base lunar intensity
        base_intensity = max_lunar_intensity * lunar_phase * lunar_elevation
        
        # Apply weather influence if enabled
        if weather_influence:
            # Get location from config for weather lookup
            latitude = config.get("latitude", 0.0)
            longitude = config.get("longitude", 0.0)
            
            if latitude != 0.0 and longitude != 0.0:
                weather_factor = await self._get_weather_factor(latitude, longitude)
                base_intensity *= weather_factor
            
        return base_intensity

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
        # Extract configuration parameters
        moonlight_start_hour = config.get("moonlight_start_hour", 20.0)
        moonlight_end_hour = config.get("moonlight_end_hour", 6.0)
        lunar_phase_influence = config.get("lunar_phase_influence", True)
        weather_influence = config.get("weather_influence", True)
        
        # Calculate current time in hours
        current_hour = current_time.hour + current_time.minute / 60.0
        
        # Check if we're in moonlight period
        if self._is_moonlight_period(current_hour, moonlight_start_hour, moonlight_end_hour):
            # Calculate base moonlight intensity
            base_intensity = 0.2  # Base moonlight level
            
            # Apply lunar phase influence
            if lunar_phase_influence:
                lunar_phase = self._calculate_lunar_phase(current_time)
                base_intensity *= lunar_phase
                
            # Apply weather influence
            if weather_influence:
                # Get location from config for weather lookup
                latitude = config.get("latitude", 0.0)
                longitude = config.get("longitude", 0.0)
                
                if latitude != 0.0 and longitude != 0.0:
                    weather_factor = await self._get_weather_factor(latitude, longitude)
                    base_intensity *= weather_factor
                
            return base_intensity
        else:
            return 0.0

    def _calculate_circadian_intensity(
        self, config: Dict[str, Any], current_time: datetime
    ) -> float:
        """
        Calculate intensity for Circadian behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            
        Returns:
            Circadian intensity value (0.0-1.0)
        """
        # Extract configuration parameters
        photoperiod = config.get("photoperiod", 12.0)  # hours of light
        peak_time = config.get("peak_time", 12.0)  # hour of peak intensity
        species_pattern = config.get("species_pattern", "standard")
        
        # Validate parameters
        photoperiod = max(6.0, min(18.0, photoperiod))
        peak_time = max(0.0, min(23.0, peak_time))
        
        # Calculate current time in hours
        current_hour = current_time.hour + current_time.minute / 60.0
        
        # Calculate circadian rhythm based on photoperiod
        if photoperiod <= 12.0:
            # Short day pattern
            if current_hour < peak_time - photoperiod/2 or current_hour > peak_time + photoperiod/2:
                return 0.0
            else:
                # Calculate intensity based on distance from peak
                distance_from_peak = abs(current_hour - peak_time)
                progress = 1.0 - (distance_from_peak / (photoperiod/2))
                return max(0.0, min(1.0, progress))
        else:
            # Long day pattern
            if current_hour < peak_time - photoperiod/2:
                current_hour += 24.0  # Wrap around
            elif current_hour > peak_time + photoperiod/2:
                current_hour -= 24.0  # Wrap around
                
            if peak_time - photoperiod/2 <= current_hour <= peak_time + photoperiod/2:
                # Calculate intensity based on distance from peak
                distance_from_peak = abs(current_hour - peak_time)
                progress = 1.0 - (distance_from_peak / (photoperiod/2))
                return max(0.0, min(1.0, progress))
            else:
                return 0.0

    async def _calculate_location_based_intensity(
        self, config: Dict[str, Any], current_time: datetime
    ) -> float:
        """
        Calculate intensity for LocationBased behavior type.
        
        Args:
            config: Behavior configuration
            current_time: Current UTC time
            
        Returns:
            Location-based intensity value (0.0-1.0)
        """
        # Extract configuration parameters
        latitude = config.get("latitude", 0.0)
        longitude = config.get("longitude", 0.0)
        location_name = config.get("location_name", "Default")
        weather_influence = config.get("weather_influence", True)
        
        # Validate parameters
        latitude = max(-90.0, min(90.0, latitude))
        longitude = max(-180.0, min(180.0, longitude))
        
        # Calculate location-specific sunrise/sunset times
        sunrise_hour, sunset_hour = self._calculate_location_sun_times(
            latitude, longitude, current_time
        )
        
        # Use diurnal calculation with location-specific times
        diurnal_config = {
            "sunrise_hour": sunrise_hour,
            "sunset_hour": sunset_hour,
            "peak_intensity": config.get("peak_intensity", 1.0),
            "min_intensity": config.get("min_intensity", 0.0),
            "ramp_duration": config.get("ramp_duration", 2.0),
        }
        
        base_intensity = self._calculate_diurnal_intensity(diurnal_config, current_time)
        
        # Apply weather influence if enabled
        if weather_influence:
            weather_factor = await self._get_weather_factor(latitude, longitude)
            base_intensity *= weather_factor
            
        return base_intensity

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
        # Extract configuration parameters
        override_intensity = config.get("override_intensity", 0.5)
        override_duration = config.get("override_duration", 60)  # minutes
        override_priority = config.get("override_priority", 10)
        
        # Validate parameters
        override_intensity = max(0.0, min(1.0, override_intensity))
        override_duration = max(1, min(1440, override_duration))  # 1 minute to 24 hours
        override_priority = max(1, min(100, override_priority))
        
        # Check if override is still valid (simplified - would need start time in config)
        # For now, assume override is always active
        return override_intensity

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
        # Extract configuration parameters
        effect_type = config.get("effect_type", "fade")
        effect_duration = config.get("effect_duration", 60)  # minutes
        effect_parameters = config.get("effect_parameters", {})
        
        # Validate parameters
        effect_duration = max(1, min(1440, effect_duration))  # 1 minute to 24 hours
        
        # Calculate effect based on type
        if effect_type == "fade":
            return self._calculate_fade_effect(effect_parameters, current_time)
        elif effect_type == "pulse":
            return self._calculate_pulse_effect(effect_parameters, current_time)
        elif effect_type == "storm":
            return self._calculate_storm_effect(effect_parameters, current_time)
        else:
            return 0.0

    # Helper methods for calculations

    def _smooth_ramp(self, progress: float) -> float:
        """Apply smooth ramp function to progress (0.0-1.0)."""
        # Use smoothstep function for natural-looking ramps
        return 3 * progress * progress - 2 * progress * progress * progress

    def _calculate_lunar_phase(self, current_time: datetime) -> float:
        """
        Calculate lunar phase using astral library.
        
        Args:
            current_time: Current UTC time
            
        Returns:
            Lunar phase intensity (0.0 = new moon, 1.0 = full moon)
        """
        try:
            # Get lunar phase from astral library (0-27 days)
            moon_phase_day = phase(current_time)
            
            # Convert 0-27 value to 0.0-1.0 intensity scale
            # Full moon is around day 14, so we calculate distance from full moon
            distance_from_full = abs(14 - moon_phase_day)
            
            # Use a smooth function to convert distance to intensity
            # At full moon (distance = 0): intensity = 1.0
            # At new moon (distance = 14): intensity = 0.0
            intensity = max(0.0, 1.0 - (distance_from_full / 14.0))
            
            return intensity
            
        except Exception as e:
            # Fallback to simplified calculation if astral library fails
            days_since_new_moon = (current_time - datetime(2024, 1, 1)).days % 29.53
            phase_radians = (days_since_new_moon / 29.53) * 2 * math.pi
            return (math.sin(phase_radians) + 1) / 2

    def _calculate_lunar_elevation(self, current_time: datetime) -> float:
        """Calculate lunar elevation (0.0 = below horizon, 1.0 = zenith)."""
        # Simplified lunar elevation calculation
        # In reality, this would use astronomical algorithms
        hour = current_time.hour
        # Assume moon is highest around midnight
        elevation = math.sin((hour - 12) * math.pi / 12)
        return max(0.0, elevation)

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

    def _is_moonlight_period(self, current_hour: float, start_hour: float, end_hour: float) -> bool:
        """Check if current time is within moonlight period."""
        if start_hour < end_hour:
            # Same day period
            return start_hour <= current_hour <= end_hour
        else:
            # Overnight period
            return current_hour >= start_hour or current_hour <= end_hour

    def _calculate_location_sun_times(self, latitude: float, longitude: float, current_time: datetime) -> tuple[float, float]:
        """
        Calculate sunrise and sunset times for a location using astral library.
        
        Args:
            latitude: Location latitude in degrees
            longitude: Location longitude in degrees
            current_time: Current UTC time
            
        Returns:
            Tuple of (sunrise_hour, sunset_hour) as float values
        """
        try:
            # Create an Observer instance with the provided coordinates
            observer = Observer(latitude=latitude, longitude=longitude)
            
            # Get solar events for the current date
            solar_events = sun(observer.observer, date=current_time.date(), tzinfo=timezone.utc)
            
            # Extract sunrise and sunset times
            sunrise_time = solar_events['sunrise']
            sunset_time = solar_events['sunset']
            
            # Convert to hours as float values
            sunrise_hour = sunrise_time.hour + sunrise_time.minute / 60.0 + sunrise_time.second / 3600.0
            sunset_hour = sunset_time.hour + sunset_time.minute / 60.0 + sunset_time.second / 3600.0
            
            return sunrise_hour, sunset_hour
            
        except Exception as e:
            # Fallback to simplified calculation if astral library fails
            # This could happen with invalid coordinates or extreme latitudes
            if abs(latitude) < 30:
                # Tropical region
                return 6.0, 18.0
            elif abs(latitude) < 60:
                # Temperate region
                return 7.0, 17.0
            else:
                # Polar region
                return 8.0, 16.0

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