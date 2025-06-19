import asyncio
from typing import Dict, Any
from shared.core.config import settings

class SensorController:
    def __init__(self):
        self.sensors: Dict[str, Any] = {}
        self.readings: Dict[str, float] = {}
        self._polling_task = None

    async def start_polling(self):
        """
        Start background polling of sensors
        """
        if self._polling_task is None:
            self._polling_task = asyncio.create_task(self._poll_loop())

    async def stop_polling(self):
        """
        Stop background polling
        """
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None

    async def _poll_loop(self):
        """
        Background task to poll sensors
        """
        while True:
            try:
                # TODO: Implement actual sensor reading logic
                # This is a placeholder for demonstration
                for sensor_id in self.sensors:
                    self.readings[sensor_id] = 0.0
                
                await asyncio.sleep(settings.SENSOR_POLL_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error polling sensors: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    def get_reading(self, sensor_id: str) -> float:
        """
        Get latest reading for a sensor
        """
        return self.readings.get(sensor_id, 0.0)

    def get_all_readings(self) -> Dict[str, float]:
        """
        Get latest readings for all sensors
        """
        return self.readings.copy() 