import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import board
import adafruit_dht
from w1thermsensor import W1ThermSensor
from app.hardware.device_base import BaseDevice, PollResult

class TemperatureSensor(BaseDevice):
    """
    Temperature sensor device supporting multiple sensor types:
    - DS18B20 (1-Wire)
    - DHT22/DHT11 (Digital)
    - I2C sensors (future)
    """
    
    def __init__(self, device_id: int, name: str, address: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(device_id, name, address, config)
        self.sensor_type = self.config.get("sensor_type", "ds18b20")
        self.sensor = None
        self._initialize_sensor()
    
    def _initialize_sensor(self):
        """Initialize the sensor based on type and address"""
        try:
            if self.sensor_type == "ds18b20":
                # DS18B20 uses the address as the sensor ID
                self.sensor = W1ThermSensor(sensor_id=self.address)
                self.logger.info(f"Initialized DS18B20 sensor: {self.address}")
                
            elif self.sensor_type in ["dht22", "dht11"]:
                # DHT sensors use GPIO pin number
                pin_number = int(self.address)
                if self.sensor_type == "dht22":
                    self.sensor = adafruit_dht.DHT22(getattr(board, f"D{pin_number}"))
                else:
                    self.sensor = adafruit_dht.DHT11(getattr(board, f"D{pin_number}"))
                self.logger.info(f"Initialized {self.sensor_type.upper()} sensor on pin {pin_number}")
                
            else:
                raise ValueError(f"Unsupported sensor type: {self.sensor_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize sensor: {e}")
            self.sensor = None
    
    async def poll(self) -> PollResult:
        """Read temperature from the sensor"""
        if not self.sensor:
            return PollResult(
                success=False,
                error="Sensor not initialized",
                timestamp=datetime.now(timezone.utc)
            )
        
        try:
            if self.sensor_type == "ds18b20":
                temperature = self.sensor.get_temperature()
                metadata = {
                    "sensor_type": "ds18b20",
                    "sensor_id": self.address,
                    "unit": "C",
                    "measurement_type": "temperature"
                }
                
            elif self.sensor_type in ["dht22", "dht11"]:
                # DHT sensors provide both temperature and humidity
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity
                
                metadata = {
                    "sensor_type": self.sensor_type,
                    "pin": self.address,
                    "temperature_unit": "C",
                    "humidity_unit": "%",
                    "measurement_type": "temperature_and_humidity"
                }
                
                # Return both values as JSON
                return PollResult(
                    success=True,
                    json_value={
                        "temperature": temperature,
                        "humidity": humidity
                    },
                    metadata=metadata,
                    timestamp=datetime.now(timezone.utc)
                )
            
            return PollResult(
                success=True,
                value=temperature,
                metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return PollResult(
                success=False,
                error=f"Failed to read temperature: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def test_connection(self) -> bool:
        """Test if the sensor is responding"""
        if not self.sensor:
            return False
        
        try:
            # Try to read a value to test connection
            if self.sensor_type == "ds18b20":
                self.sensor.get_temperature()
            elif self.sensor_type in ["dht22", "dht11"]:
                self.sensor.temperature  # This will raise an exception if not connected
            return True
            
        except Exception as e:
            self.logger.debug(f"Connection test failed: {e}")
            return False 