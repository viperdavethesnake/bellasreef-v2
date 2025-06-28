"""
HAL Service for Lighting Integration.

This module provides a service layer that bridges the lighting behavior runner
with the hardware abstraction layer (HAL). It handles intensity to duty cycle
conversion, channel mapping, and hardware writes while maintaining proper
logging and error handling.
"""
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime
import asyncio
from shared.utils.logger import get_logger

# Import HAL driver functions
from ..drivers.pca9685_driver import (
    perform_synchronous_hardware_write,
    set_multiple_channels_duty_cycle,
    get_current_duty_cycle,
    get_manager_status
)

logger = get_logger(__name__)


class LightingHALService:
    """
    HAL service for lighting integration.
    
    This service provides methods to:
    - Convert lighting intensities to hardware duty cycles
    - Write intensity values to hardware channels
    - Read current hardware states
    - Handle bulk channel updates
    - Provide hardware status information
    
    All hardware operations are performed through the HAL layer to maintain
    proper abstraction and error handling.
    """
    
    def __init__(self):
        """Initialize the lighting HAL service."""
        self._channel_mapping: Dict[int, Tuple[int, int]] = {}  # channel_id -> (controller_address, channel_number)
        self._intensity_cache: Dict[int, float] = {}  # channel_id -> last_intensity
        self._hardware_available = True
        
    def register_channel(self, channel_id: int, controller_address: Any, channel_number: Any) -> bool:
        try:
            # Explicitly cast to int to handle string inputs
            addr = int(controller_address)
            chan = int(channel_number)
        except (ValueError, TypeError):
            logger.error(f"Invalid non-integer value for address or channel: addr={controller_address}, chan={channel_number}")
            return False

        if not 0 <= chan <= 15:
            logger.error(f"Channel number out of range: {chan}")
            return False  # Return False instead of raising an exception
        if not 0x40 <= addr <= 0x7F:
            logger.error(f"Controller address out of range: {hex(addr)}")
            return False  # Return False instead of raising an exception

        self._channel_mapping[channel_id] = (addr, chan)
        logger.info(f"Registered lighting channel {channel_id} -> I2C:{hex(addr)} Ch:{chan}")
        return True
        
    def unregister_channel(self, channel_id: int) -> bool:
        """
        Unregister a lighting channel.
        
        Args:
            channel_id: Lighting system channel identifier
            
        Returns:
            True if channel was registered and removed, False otherwise
        """
        if channel_id in self._channel_mapping:
            controller_address, channel_number = self._channel_mapping[channel_id]
            del self._channel_mapping[channel_id]
            if channel_id in self._intensity_cache:
                del self._intensity_cache[channel_id]
            logger.info(f"Unregistered lighting channel {channel_id} -> I2C:{hex(controller_address)} Ch:{channel_number}")
            return True
        return False
        
    def get_registered_channels(self) -> List[int]:
        """
        Get list of registered channel IDs.
        
        Returns:
            List of registered channel IDs
        """
        return list(self._channel_mapping.keys())
        
    def _intensity_to_duty_cycle(self, intensity: float) -> int:
        """
        Convert lighting intensity (0.0-1.0) to hardware duty cycle (0-65535).
        
        Args:
            intensity: Lighting intensity as float 0.0-1.0
            
        Returns:
            Hardware duty cycle as integer 0-65535
        """
        if not 0.0 <= intensity <= 1.0:
            raise ValueError(f"Intensity must be 0.0-1.0, got {intensity}")
            
        # Convert to 16-bit duty cycle
        duty_cycle = int(intensity * 65535)
        return max(0, min(65535, duty_cycle))  # Ensure bounds
        
    def _duty_cycle_to_intensity(self, duty_cycle: int) -> float:
        """
        Convert hardware duty cycle (0-65535) to lighting intensity (0.0-1.0).
        
        Args:
            duty_cycle: Hardware duty cycle as integer 0-65535
            
        Returns:
            Lighting intensity as float 0.0-1.0
        """
        if not 0 <= duty_cycle <= 65535:
            raise ValueError(f"Duty cycle must be 0-65535, got {duty_cycle}")
            
        return duty_cycle / 65535.0
        
    def write_channel_intensity(
        self, 
        channel_id: int, 
        intensity: float,
        log_context: Optional[Dict] = None
    ) -> bool:
        """
        Write intensity value to a single channel.
        
        Args:
            channel_id: Lighting system channel identifier
            intensity: Desired intensity (0.0-1.0)
            log_context: Optional context for logging (e.g., behavior_id, assignment_id)
            
        Returns:
            True if successful, False otherwise
        """
        if channel_id not in self._channel_mapping:
            logger.error(f"Channel {channel_id} not registered with HAL service")
            return False
            
        try:
            controller_address, channel_number = self._channel_mapping[channel_id]
            duty_cycle = self._intensity_to_duty_cycle(intensity)
            
            # Check if value has changed
            if channel_id in self._intensity_cache and self._intensity_cache[channel_id] == intensity:
                logger.debug(f"HAL_SKIP: Channel {channel_id} intensity {intensity} unchanged")
                return True
                
            # Perform hardware write
            success = perform_synchronous_hardware_write(
                address=controller_address,
                channel=channel_number,
                duty_cycle=duty_cycle
            )
            
            if success:
                self._intensity_cache[channel_id] = intensity
                log_msg = f"HAL_WRITE: Channel {channel_id} -> I2C:{hex(controller_address)} Ch:{channel_number} Intensity:{intensity:.3f} DutyCycle:{duty_cycle}"
                if log_context:
                    log_msg += f" Context:{log_context}"
                logger.info(log_msg)
            else:
                logger.error(f"HAL_WRITE_FAILED: Channel {channel_id} -> I2C:{hex(controller_address)} Ch:{channel_number} Intensity:{intensity}")
                
            return success
            
        except Exception as e:
            logger.error(f"HAL_WRITE_ERROR: Channel {channel_id} Intensity:{intensity} Error:{type(e).__name__}: {e}")
            return False
            
    def write_multiple_channels(
        self, 
        channel_intensities: Dict[int, float],
        log_context: Optional[Dict] = None
    ) -> Dict[int, bool]:
        """
        Write intensity values to multiple channels efficiently.
        
        Args:
            channel_intensities: Dictionary mapping channel_id to intensity (0.0-1.0)
            log_context: Optional context for logging
            
        Returns:
            Dictionary mapping channel_id to success status
        """
        if not channel_intensities:
            return {}
            
        results = {}
        
        # Group channels by controller for bulk operations
        controller_channels: Dict[int, Dict[int, int]] = {}  # controller_address -> {channel_number: duty_cycle}
        single_channels: Dict[int, Tuple[int, int, float]] = {}  # channel_id -> (controller_address, channel_number, intensity)
        
        for channel_id, intensity in channel_intensities.items():
            if channel_id not in self._channel_mapping:
                logger.error(f"Channel {channel_id} not registered with HAL service")
                results[channel_id] = False
                continue
                
            controller_address, channel_number = self._channel_mapping[channel_id]
            duty_cycle = self._intensity_to_duty_cycle(intensity)
            
            # Check if value has changed
            if channel_id in self._intensity_cache and self._intensity_cache[channel_id] == intensity:
                logger.debug(f"HAL_BULK_SKIP: Channel {channel_id} intensity {intensity} unchanged")
                results[channel_id] = True
                continue
                
            # Group by controller for bulk operations
            if controller_address not in controller_channels:
                controller_channels[controller_address] = {}
            controller_channels[controller_address][channel_number] = duty_cycle
            single_channels[channel_id] = (controller_address, channel_number, intensity)
            
        # Perform bulk writes for each controller
        for controller_address, channel_duty_cycles in controller_channels.items():
            try:
                if len(channel_duty_cycles) > 1:
                    # Bulk write for multiple channels on same controller
                    set_multiple_channels_duty_cycle(controller_address, channel_duty_cycles)
                    
                    # Mark all channels as successful
                    for channel_number in channel_duty_cycles:
                        # Find channel_id for this channel_number
                        for ch_id, (addr, ch_num, intensity) in single_channels.items():
                            if addr == controller_address and ch_num == channel_number:
                                results[ch_id] = True
                                self._intensity_cache[ch_id] = intensity
                                break
                                
                    log_msg = f"HAL_BULK_WRITE: I2C:{hex(controller_address)} Channels:{len(channel_duty_cycles)}"
                    if log_context:
                        log_msg += f" Context:{log_context}"
                    logger.info(log_msg)
                    
                else:
                    # Single channel write
                    channel_number = list(channel_duty_cycles.keys())[0]
                    duty_cycle = channel_duty_cycles[channel_number]
                    
                    success = perform_synchronous_hardware_write(
                        address=controller_address,
                        channel=channel_number,
                        duty_cycle=duty_cycle
                    )
                    
                    # Find channel_id for this channel_number
                    for ch_id, (addr, ch_num, intensity) in single_channels.items():
                        if addr == controller_address and ch_num == channel_number:
                            results[ch_id] = success
                            if success:
                                self._intensity_cache[ch_id] = intensity
                            break
                            
            except Exception as e:
                logger.error(f"HAL_BULK_ERROR: I2C:{hex(controller_address)} Error:{type(e).__name__}: {e}")
                # Mark all channels for this controller as failed
                for ch_id, (addr, ch_num, intensity) in single_channels.items():
                    if addr == controller_address:
                        results[ch_id] = False
                        
        return results
        
    def read_channel_intensity(self, channel_id: int) -> Optional[float]:
        """
        Read current intensity value from hardware for a channel.
        
        Args:
            channel_id: Lighting system channel identifier
            
        Returns:
            Current intensity (0.0-1.0) or None if error
        """
        if channel_id not in self._channel_mapping:
            logger.error(f"Channel {channel_id} not registered with HAL service")
            return None
            
        try:
            controller_address, channel_number = self._channel_mapping[channel_id]
            duty_cycle = get_current_duty_cycle(controller_address, channel_number)
            intensity = self._duty_cycle_to_intensity(duty_cycle)
            
            logger.debug(f"HAL_READ: Channel {channel_id} -> I2C:{hex(controller_address)} Ch:{channel_number} Intensity:{intensity:.3f}")
            return intensity
            
        except Exception as e:
            logger.error(f"HAL_READ_ERROR: Channel {channel_id} Error:{type(e).__name__}: {e}")
            return None
            
    def get_hardware_status(self) -> Dict:
        """
        Get hardware manager status information.
        
        Returns:
            Dictionary containing hardware status information
        """
        try:
            status = get_manager_status()
            return {
                "hardware_available": self._hardware_available,
                "registered_channels": len(self._channel_mapping),
                "channel_mappings": {
                    str(ch_id): {
                        "controller_address": hex(addr),
                        "channel_number": ch_num
                    }
                    for ch_id, (addr, ch_num) in self._channel_mapping.items()
                },
                "manager_status": status
            }
        except Exception as e:
            logger.error(f"HAL_STATUS_ERROR: {type(e).__name__}: {e}")
            return {
                "hardware_available": False,
                "registered_channels": len(self._channel_mapping),
                "error": str(e)
            }
            
    def is_hardware_available(self) -> bool:
        """
        Check if hardware is available.
        
        Returns:
            True if hardware is available, False otherwise
        """
        return self._hardware_available


# Global singleton instance
_lighting_hal_service: Optional[LightingHALService] = None


def get_lighting_hal_service() -> LightingHALService:
    """
    Get the global singleton lighting HAL service instance.
    
    Returns:
        LightingHALService instance
    """
    global _lighting_hal_service
    if _lighting_hal_service is None:
        _lighting_hal_service = LightingHALService()
    return _lighting_hal_service


def cleanup_lighting_hal_service() -> None:
    """Clean up the global lighting HAL service instance."""
    global _lighting_hal_service
    if _lighting_hal_service is not None:
        # Clear all registrations
        for channel_id in list(_lighting_hal_service._channel_mapping.keys()):
            _lighting_hal_service.unregister_channel(channel_id)
        _lighting_hal_service = None
        logger.info("Lighting HAL service cleaned up") 