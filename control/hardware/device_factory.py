import importlib
from typing import Dict, Type, Optional
import logging
from control.hardware.device_base import BaseDevice

logger = logging.getLogger(__name__)

class DeviceFactory:
    """
    Factory for creating device instances based on device type.
    Supports dynamic loading of device plugins.
    """
    
    # Registry of known device types and their classes
    _device_registry: Dict[str, Type[BaseDevice]] = {}
    
    @classmethod
    def register_device_type(cls, device_type: str, device_class: Type[BaseDevice]):
        """Register a device type with its implementation class"""
        cls._device_registry[device_type] = device_class
        logger.info(f"Registered device type: {device_type} -> {device_class.__name__}")
    
    @classmethod
    def get_device_class(cls, device_type: str) -> Optional[Type[BaseDevice]]:
        """Get the device class for a given device type"""
        return cls._device_registry.get(device_type)
    
    @classmethod
    def create_device(
        cls, 
        device_type: str, 
        device_id: int, 
        name: str, 
        address: str, 
        config: Optional[Dict] = None
    ) -> Optional[BaseDevice]:
        """
        Create a device instance of the specified type.
        
        Args:
            device_type: Type of device (e.g., 'temperature_sensor', 'outlet')
            device_id: Database ID of the device
            name: Device name
            address: Device address/identifier
            config: Device-specific configuration
            
        Returns:
            BaseDevice instance or None if device type not found
        """
        device_class = cls.get_device_class(device_type)
        
        if not device_class:
            logger.error(f"Unknown device type: {device_type}")
            return None
        
        try:
            device = device_class(device_id, name, address, config)
            logger.info(f"Created device: {name} ({device_type})")
            return device
            
        except Exception as e:
            logger.error(f"Failed to create device {name} ({device_type}): {e}")
            return None
    
    @classmethod
    def get_available_device_types(cls) -> list[str]:
        """Get list of all registered device types"""
        return list(cls._device_registry.keys())
    
    @classmethod
    def load_device_plugins(cls):
        """Load all device plugins from the devices directory"""
        try:
            # Import and register built-in device types
            from control.hardware.devices.temperature_sensor import TemperatureSensor
            from control.hardware.devices.outlet import Outlet
            
            cls.register_device_type("temperature_sensor", TemperatureSensor)
            cls.register_device_type("outlet", Outlet)
            
            logger.info("Loaded built-in device plugins")
            
        except ImportError as e:
            logger.warning(f"Failed to load some device plugins: {e}")
    
    @classmethod
    def load_custom_device_plugin(cls, module_path: str, class_name: str, device_type: str):
        """
        Load a custom device plugin from a module.
        
        Args:
            module_path: Python module path (e.g., 'my_plugins.custom_sensor')
            class_name: Name of the device class
            device_type: Device type identifier
        """
        try:
            module = importlib.import_module(module_path)
            device_class = getattr(module, class_name)
            
            if not issubclass(device_class, BaseDevice):
                raise ValueError(f"{class_name} must inherit from BaseDevice")
            
            cls.register_device_type(device_type, device_class)
            logger.info(f"Loaded custom device plugin: {device_type} from {module_path}.{class_name}")
            
        except Exception as e:
            logger.error(f"Failed to load custom device plugin {device_type}: {e}")

# Initialize the factory with built-in devices
DeviceFactory.load_device_plugins() 