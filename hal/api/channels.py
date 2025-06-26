from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from typing import Optional, List

from shared.db.database import get_db
from shared.crud import device as device_crud
from shared.schemas.enums import DeviceRole
from shared.schemas.user import User
from shared.schemas import device as device_schema
from shared.utils.logger import get_logger
from core.api.deps import get_current_user

from ..drivers import pca9685_driver
from .schemas import PWMControlRequest, PWMControlRequestWithDevice

logger = get_logger(__name__)

router = APIRouter(prefix="/channels", tags=["Channels"])

async def _perform_ramp(
    db: AsyncSession, 
    device_id: int, 
    start_intensity: float, 
    end_intensity: int, 
    duration_ms: int,
    controller_address: int,
    channel_number: int
):
    """
    Background worker function to perform a gradual ramp from start_intensity to end_intensity
    over the specified duration in milliseconds.
    """
    # Calculate ramp parameters
    step_interval_ms = 50  # Update every 50ms for smooth transition
    total_steps = duration_ms // step_interval_ms
    intensity_change_per_step = (end_intensity - start_intensity) / total_steps
    
    # Get the device for database updates
    channel_device = await device_crud.get(db, device_id=device_id)
    if not channel_device:
        return  # Device no longer exists
    
    # Perform the ramp
    for step in range(total_steps + 1):  # +1 to include the final step
        # Calculate current intensity for this step
        current_intensity = start_intensity + (intensity_change_per_step * step)
        
        # Ensure we reach exactly the target intensity on the final step
        if step == total_steps:
            current_intensity = end_intensity
        
        # Convert intensity to duty cycle
        duty_cycle = int((current_intensity / 100) * 65535)
        
        try:
            # Update hardware
            pca9685_driver.set_channel_duty_cycle(
                address=controller_address,
                channel=channel_number,
                duty_cycle=duty_cycle
            )
            
            # Update database with current value
            channel_device.current_value = current_intensity
            db.add(channel_device)
            await db.commit()
            
        except Exception as e:
            # Log error but continue with ramp
            logger.error(
                f"Error during ramp step {step} for device {device_id} (Channel {channel_number}): {e}",
                exc_info=True
            )
            break
        
        # Sleep for the step interval (except on the last step)
        if step < total_steps:
            await asyncio.sleep(step_interval_ms / 1000.0)  # Convert ms to seconds

@router.post("/{channel_id}/control", status_code=status.HTTP_200_OK)
async def set_pwm_channel_duty_cycle(
    channel_id: int,
    request: PWMControlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sets the intensity (duty cycle) for a configured PWM channel device.
    """
    # 1. Fetch the channel device from the database
    channel_device = await device_crud.get(db, device_id=channel_id)
    if not channel_device or channel_device.role != DeviceRole.PWM_CHANNEL.value:
        raise HTTPException(status_code=404, detail="PWM Channel device not found.")

    # 2. Get the parent controller to find its address
    if not channel_device.parent_device_id:
        raise HTTPException(status_code=400, detail="Channel device is not linked to a parent controller.")
    
    parent_controller = await device_crud.get(db, device_id=channel_device.parent_device_id)
    if not parent_controller:
        raise HTTPException(status_code=404, detail="Parent controller not found for this channel.")

    # 3. Get hardware-specific info from the config fields
    controller_address = int(parent_controller.address)
    channel_number = channel_device.config.get("channel_number")

    if channel_number is None:
        raise HTTPException(status_code=500, detail="Channel number is not configured for this device.")

    # 4. Apply min/max constraints and convert intensity (0-100) to 16-bit duty cycle (0-65535)
    constrained_intensity = max(channel_device.min_value, min(channel_device.max_value, request.intensity))

    if request.duration_ms and request.duration_ms > 0:
        # This is a ramped request
        start_intensity = channel_device.current_value or 0.0
        
        # Add the ramp task to background tasks
        background_tasks.add_task(
            _perform_ramp,
            db=db,
            device_id=channel_id,
            start_intensity=start_intensity,
            end_intensity=constrained_intensity,
            duration_ms=request.duration_ms,
            controller_address=controller_address,
            channel_number=channel_number
        )
        
        return {
            "message": f"Ramp initiated for device '{channel_device.name}' (Channel {channel_number}): {start_intensity}% → {constrained_intensity}% over {request.duration_ms}ms",
            "ramp_started": True,
            "start_intensity": start_intensity,
            "target_intensity": constrained_intensity,
            "duration_ms": request.duration_ms
        }
    else:
        # This is an immediate request
        duty_cycle = int((constrained_intensity / 100) * 65535)

        # 5. Call the driver to set the hardware state
        try:
            pca9685_driver.set_channel_duty_cycle(
                address=controller_address,
                channel=channel_number,
                duty_cycle=duty_cycle
            )
            
            # Update the device's current_value in the database
            channel_device.current_value = constrained_intensity
            db.add(channel_device)
            await db.commit()
            
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to set PWM channel duty cycle. Hardware error: {e}")

        return {
            "message": f"Successfully set device '{channel_device.name}' (Channel {channel_number}) to {constrained_intensity}% intensity.", 
            "duty_cycle_value": duty_cycle,
            "current_value": constrained_intensity
        }

@router.post("/bulk-control", status_code=status.HTTP_200_OK, summary="Control Multiple PWM Channels")
async def bulk_set_pwm_duty_cycle(
    requests: List[PWMControlRequestWithDevice],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sets the intensity for multiple PWM channels in a single request.
    Supports both immediate and ramped changes.
    """
    results = []
    devices_to_update = []

    for request in requests:
        try:
            # 1. Fetch the channel device from the database
            channel_device = await device_crud.get(db, device_id=request.device_id)
            if not channel_device or channel_device.role != DeviceRole.PWM_CHANNEL.value:
                results.append({"device_id": request.device_id, "status": "error", "detail": "PWM Channel device not found."})
                continue

            # 2. Get the parent controller to find its address
            if not channel_device.parent_device_id:
                results.append({"device_id": request.device_id, "status": "error", "detail": "Channel device is not linked to a parent controller."})
                continue
            
            parent_controller = await device_crud.get(db, device_id=channel_device.parent_device_id)
            if not parent_controller:
                results.append({"device_id": request.device_id, "status": "error", "detail": "Parent controller not found for this channel."})
                continue

            # 3. Get hardware-specific info from the config fields
            controller_address = int(parent_controller.address)
            channel_number = channel_device.config.get("channel_number")

            if channel_number is None:
                results.append({"device_id": request.device_id, "status": "error", "detail": "Channel number is not configured for this device."})
                continue

            # 4. Apply min/max constraints and convert intensity (0-100) to 16-bit duty cycle (0-65535)
            constrained_intensity = max(channel_device.min_value, min(channel_device.max_value, request.intensity))

            if request.duration_ms and request.duration_ms > 0:
                # Handle ramped request
                start_intensity = channel_device.current_value or 0.0
                
                # Add the ramp task to background tasks
                background_tasks.add_task(
                    _perform_ramp,
                    db=db,
                    device_id=request.device_id,
                    start_intensity=start_intensity,
                    end_intensity=constrained_intensity,
                    duration_ms=request.duration_ms,
                    controller_address=controller_address,
                    channel_number=channel_number
                )
                
                results.append({
                    "device_id": request.device_id, 
                    "status": "success", 
                    "detail": f"Ramp initiated: {start_intensity}% → {constrained_intensity}% over {request.duration_ms}ms"
                })
            else:
                # Handle immediate request
                duty_cycle = int((constrained_intensity / 100) * 65535)
                
                try:
                    # Call the driver to set the hardware state
                    pca9685_driver.set_channel_duty_cycle(
                        address=controller_address,
                        channel=channel_number,
                        duty_cycle=duty_cycle
                    )
                    
                    # Mark device for database update
                    channel_device.current_value = constrained_intensity
                    devices_to_update.append(channel_device)
                    
                    results.append({
                        "device_id": request.device_id, 
                        "status": "success", 
                        "detail": f"Set to {constrained_intensity}% intensity"
                    })
                    
                except Exception as e:
                    results.append({
                        "device_id": request.device_id, 
                        "status": "error", 
                        "detail": f"Hardware error: {str(e)}"
                    })

        except Exception as e:
            results.append({"device_id": request.device_id, "status": "error", "detail": str(e)})

    # Commit all database updates in a single transaction
    if devices_to_update:
        db.add_all(devices_to_update)
        await db.commit()

    return results

@router.get("/{channel_id}/state", response_model=float, summary="Get Current PWM Channel State")
async def get_pwm_channel_state(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Gets the last known intensity for a configured PWM channel device from the database.
    """
    channel_device = await device_crud.get(db, device_id=channel_id)
    if not channel_device or channel_device.role != DeviceRole.PWM_CHANNEL.value:
        raise HTTPException(status_code=404, detail="PWM Channel device not found.")

    return channel_device.current_value

@router.get("", response_model=List[device_schema.Device], summary="List All Registered PWM Channels")
async def list_all_pwm_channels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a list of all devices configured with the 'pwm_channel' role across all controllers.
    """
    channels = await device_crud.get_multi(db, role=DeviceRole.PWM_CHANNEL.value)
    return channels 