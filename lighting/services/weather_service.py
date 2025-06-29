"""
Service for fetching and caching weather data from an external API.
"""
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any

from shared.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)

class WeatherService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.cache: Dict[str, Any] = {}
        self.cache_expiry_seconds = 600  # Cache weather for 10 minutes

    async def get_current_conditions(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get weather conditions, using a cache to avoid excessive API calls.
        Returns a dictionary with status, cloud cover, and modifier.
        """
        cache_key = f"{latitude:.3f},{longitude:.3f}"
        current_time = datetime.now()

        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if (current_time - cached_data['timestamp']).total_seconds() < self.cache_expiry_seconds:
                return cached_data['data']

        api_key = getattr(settings, 'LIGHTING_WEATHER_API_KEY', None)
        if not api_key or api_key == "changeme":
            logger.warning("Weather API key not configured. Weather influence disabled.")
            return {"status_text": "Not Configured", "cloud_cover_percent": 0, "intensity_modifier": 1.0}

        try:
            url = "https://api.openweathermap.org/data/3.0/onecall"
            params = {'lat': latitude, 'lon': longitude, 'appid': api_key, 'exclude': 'minutely,hourly,daily,alerts'}
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            cloud_percentage = data.get('current', {}).get('clouds', 0)
            status_text = data.get('current', {}).get('weather', [{}])[0].get('description', 'Unknown')
            # Intensity modifier: 1.0 for 0% clouds, 0.3 for 100% clouds
            modifier = 1.0 - (cloud_percentage / 100.0) * 0.7

            result_data = {"status_text": status_text, "cloud_cover_percent": cloud_percentage, "intensity_modifier": modifier}
            self.cache[cache_key] = {'timestamp': current_time, 'data': result_data}
            
            return result_data
            
        except Exception as e:
            logger.error(f"Weather API call failed: {e}")
            return {"status_text": "API Error", "cloud_cover_percent": 0, "intensity_modifier": 1.0}

# Create a singleton instance for use across the application
weather_service = WeatherService() 