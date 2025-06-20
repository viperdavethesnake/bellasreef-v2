import os
import glob
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from temp.config import settings
from shared.schemas.probe import ProbeDiscovery, ProbeCurrent, ProbeCheck, ProbeStatus

class TemperatureService:
    """
    Temperature service for managing 1-wire temperature sensors.
    
    This service handles:
    - 1-wire subsystem detection and validation
    - Temperature sensor discovery
    - Current temperature readings
    - Hardware status monitoring
    """
    
    def __init__(self):
        """Initialize the temperature service."""
        self.device_dir = Path(settings.W1_DEVICE_DIR)
        self.gpio_pin = settings.W1_GPIO_PIN
    
    def check_1wire_subsystem(self) -> ProbeCheck:
        """
        Check if the 1-wire subsystem is available and working.
        
        Returns:
            ProbeCheck: Status of the 1-wire subsystem
        """
        try:
            # Check if device directory exists
            if not self.device_dir.exists():
                return ProbeCheck(
                    subsystem_available=False,
                    device_count=0,
                    error="1-wire device directory not found",
                    details=f"Directory {self.device_dir} does not exist. Check if 1-wire is enabled in /boot/config.txt"
                )
            
            # Check if device directory is readable
            if not os.access(self.device_dir, os.R_OK):
                return ProbeCheck(
                    subsystem_available=False,
                    device_count=0,
                    error="1-wire device directory not readable",
                    details=f"Directory {self.device_dir} is not readable. Check permissions."
                )
            
            # Count available devices
            devices = self._discover_devices()
            device_count = len(devices)
            
            if device_count == 0:
                return ProbeCheck(
                    subsystem_available=True,
                    device_count=0,
                    error="No temperature sensors found",
                    details=f"1-wire subsystem is available but no sensors found in {self.device_dir}"
                )
            
            return ProbeCheck(
                subsystem_available=True,
                device_count=device_count,
                details=f"Found {device_count} temperature sensor(s) on GPIO {self.gpio_pin}"
            )
            
        except Exception as e:
            return ProbeCheck(
                subsystem_available=False,
                device_count=0,
                error=f"1-wire subsystem error: {str(e)}",
                details="Check hardware connections and /boot/config.txt configuration"
            )
    
    def discover_probes(self) -> List[ProbeDiscovery]:
        """
        Discover all available temperature sensors.
        
        Returns:
            List[ProbeDiscovery]: List of discovered probes
        """
        probes = []
        
        try:
            # Get list of device directories
            device_pattern = str(self.device_dir / "28-*")
            device_dirs = glob.glob(device_pattern)
            
            for device_dir in device_dirs:
                device_id = os.path.basename(device_dir)
                
                # Try to read temperature
                try:
                    temperature = self._read_temperature(device_id)
                    probes.append(ProbeDiscovery(
                        device_id=device_id,
                        available=True,
                        temperature=temperature
                    ))
                except Exception as e:
                    probes.append(ProbeDiscovery(
                        device_id=device_id,
                        available=False,
                        error=str(e)
                    ))
            
        except Exception as e:
            # If discovery fails, return empty list
            pass
        
        return probes
    
    def get_current_temperature(self, device_id: str) -> Optional[ProbeCurrent]:
        """
        Get current temperature reading for a specific device.
        
        Args:
            device_id: The 1-wire device ID
            
        Returns:
            Optional[ProbeCurrent]: Current temperature reading or None if error
        """
        try:
            temperature = self._read_temperature(device_id)
            
            return ProbeCurrent(
                probe_id=0,  # Will be set by API layer
                device_id=device_id,
                temperature=temperature,
                timestamp=datetime.utcnow(),
                status=ProbeStatus.ONLINE
            )
            
        except Exception as e:
            return ProbeCurrent(
                probe_id=0,  # Will be set by API layer
                device_id=device_id,
                temperature=0.0,
                timestamp=datetime.utcnow(),
                status=ProbeStatus.ERROR,
                error=str(e)
            )
    
    def _discover_devices(self) -> List[str]:
        """
        Discover available 1-wire devices.
        
        Returns:
            List[str]: List of device IDs
        """
        device_pattern = str(self.device_dir / "28-*")
        device_dirs = glob.glob(device_pattern)
        return [os.path.basename(d) for d in device_dirs]
    
    def _read_temperature(self, device_id: str) -> float:
        """
        Read temperature from a specific 1-wire device.
        
        Args:
            device_id: The 1-wire device ID
            
        Returns:
            float: Temperature in Celsius
            
        Raises:
            Exception: If reading fails
        """
        device_path = self.device_dir / device_id / "w1_slave"
        
        if not device_path.exists():
            raise Exception(f"Device file not found: {device_path}")
        
        # Read the device file
        with open(device_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise Exception("Invalid device file format")
        
        # Parse temperature from second line
        # Format: "t=12345" where t is temperature in millidegrees
        temp_line = lines[1].strip()
        if not temp_line.startswith("t="):
            raise Exception("Temperature data not found in device file")
        
        try:
            temp_millidegrees = int(temp_line[2:])
            temperature = temp_millidegrees / 1000.0
            return temperature
        except ValueError:
            raise Exception("Invalid temperature data format")
    
    async def get_stub_history(self, probe_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get stub historical data for a probe.
        
        This is a placeholder implementation that returns dummy data.
        Real implementation would query the database or external storage.
        
        Args:
            probe_id: The probe ID
            hours: Number of hours of history to return
            
        Returns:
            List[Dict[str, Any]]: List of historical readings
        """
        import random
        from datetime import timedelta
        
        # Generate stub data
        history = []
        base_temp = 25.0  # Base temperature in Celsius
        current_time = datetime.utcnow()
        
        for i in range(hours):
            # Generate timestamp (going backwards from current time)
            timestamp = current_time - timedelta(hours=i)
            
            # Generate temperature with some variation
            temp_variation = random.uniform(-2.0, 2.0)
            temperature = base_temp + temp_variation
            
            history.append({
                "probe_id": probe_id,
                "temperature": round(temperature, 2),
                "timestamp": timestamp.isoformat(),
                "status": "online"
            })
        
        return history[::-1]  # Reverse to get chronological order

# Create singleton instance
temperature_service = TemperatureService() 