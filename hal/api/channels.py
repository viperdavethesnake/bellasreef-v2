from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from typing import Optional, List

from shared.db.database import get_db
from shared.crud import device as device_crud
from shared.schemas.enums import DeviceRole
from shared.schemas.user import User
from shared.schemas import device as device_schema
from shared.utils.logger import get_logger
from ..deps import get_current_user_or_service

from ..drivers import pca9685_driver
from .schemas import PWMControlRequest, PWMControlRequestWithDevice, PWMChannelUpdateRequest

logger = get_logger(__name__)

router = APIRouter(prefix="/channels", tags=["Channels"])

# Global dictionary to track active ramp tasks by (controller_address, channel_number)
_active_ramp_tasks = {}

async def _perform_ramp(
    device_id: int, 
    start_intensity: float, 
    end_intensity: int, 
    duration_ms: int,
    controller_address: int,
    channel_number: int,
    curve: str = 'linear',
    step_interval_ms: int = 50
):
    """
    Background worker function to perform a gradual ramp from start_intensity to end_intensity
    over the specified duration in milliseconds.
    """
    # Create a unique key for this controller/channel combination
    ramp_key = (controller_address, channel_number)
    
    # Create and manage our own DB session
    async for db in get_db():
        # Calculate ramp parameters
        total_steps = duration_ms // step_interval_ms
        
        # Get the device for database updates
        channel_device = await device_crud.get(db, device_id=device_id)
        if not channel_device:
            return  # Device no longer exists
        
        # Determine if this is a long ramp (> 10 seconds) for intermediate DB updates
        is_long_ramp = duration_ms > 10000
        intermediate_update_interval = 2000  # 2 seconds in milliseconds
        last_db_update_time = 0
        
        # Update database at start of ramp
        channel_device.current_value = start_intensity
        db.add(channel_device)
        await db.commit()
        
        # Perform the ramp
        for step in range(total_steps + 1):  # +1 to include the final step
            # Calculate current intensity for this step based on curve type
            if curve == 'exponential':
                # Exponential curve (ease-in) for more natural lighting effects
                progress = step / total_steps
                eased_progress = progress * progress  # Quadratic ease-in
                current_intensity = start_intensity + (end_intensity - start_intensity) * eased_progress
            else:
                # Linear curve (default)
                intensity_change_per_step = (end_intensity - start_intensity) / total_steps
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
                
                # Update database only at start, end, and every 2 seconds for long ramps
                current_time = step * step_interval_ms
                should_update_db = (
                    step == 0 or  # Start of ramp
                    step == total_steps or  # End of ramp
                    (is_long_ramp and current_time - last_db_update_time >= intermediate_update_interval)  # Intermediate updates for long ramps
                )
                
                if should_update_db:
                    channel_device.current_value = current_intensity
                    db.add(channel_device)
                    await db.commit()
                    last_db_update_time = current_time
                
            except Exception as e:
                # Log error with full context
                logger.error(
                    f"Hardware error during ramp step {step}/{total_steps} for device {device_id} "
                    f"(controller={controller_address}, channel={channel_number}, "
                    f"intended_intensity={current_intensity}%, duty_cycle={duty_cycle}): {e}",
                    exc_info=True
                )
                
                # Attempt one retry for this step
                try:
                    logger.info(f"Retrying ramp step {step} for device {device_id} (controller={controller_address}, channel={channel_number})")
                    pca9685_driver.set_channel_duty_cycle(
                        address=controller_address,
                        channel=channel_number,
                        duty_cycle=duty_cycle
                    )
                    logger.info(f"Retry successful for ramp step {step} for device {device_id}")
                except Exception as retry_e:
                    logger.error(
                        f"Retry failed for ramp step {step} for device {device_id} "
                        f"(controller={controller_address}, channel={channel_number}, "
                        f"intended_intensity={current_intensity}%, duty_cycle={duty_cycle}): {retry_e}",
                        exc_info=True
                    )
                    # Abort the ramp after retry failure
                    break
            
            # Sleep for the step interval (except on the last step)
            if step < total_steps:
                await asyncio.sleep(step_interval_ms / 1000.0)  # Convert ms to seconds
        
        # Clean up the ramp task from the active tasks dictionary
        if ramp_key in _active_ramp_tasks:
            del _active_ramp_tasks[ramp_key]
        break  # Only need one session context

@router.post("/{channel_id}/control", status_code=status.HTTP_200_OK)
async def set_pwm_channel_duty_cycle(
    channel_id: int,
    request: PWMControlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Sets the intensity (duty cycle) for a configured PWM channel device.
    """
    # 1. Fetch the channel device from the database
    channel_device = await device_crud.get(db, device_id=channel_id)
    if not channel_device or channel_device.device_type != "pwm_channel":
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
        
        # Create a unique key for this controller/channel combination
        ramp_key = (controller_address, channel_number)
        
        # Cancel any existing ramp for this channel
        if ramp_key in _active_ramp_tasks:
            existing_task = _active_ramp_tasks[ramp_key]
            if not existing_task.done():
                existing_task.cancel()
                logger.info(f"Cancelled existing ramp for controller {controller_address}, channel {channel_number}")
        
        # Create and store the new ramp task
        ramp_task = asyncio.create_task(_perform_ramp(
            device_id=channel_id,
            start_intensity=start_intensity,
            end_intensity=constrained_intensity,
            duration_ms=request.duration_ms,
            controller_address=controller_address,
            channel_number=channel_number,
            curve=request.curve,
            step_interval_ms=request.step_interval_ms
        ))
        _active_ramp_tasks[ramp_key] = ramp_task
        
        return {
            "message": f"Ramp initiated for device '{channel_device.name}' (Channel {channel_number}): {start_intensity}% → {constrained_intensity}% over {request.duration_ms}ms",
            "ramp_started": True,
            "start_intensity": start_intensity,
            "target_intensity": constrained_intensity,
            "duration_ms": request.duration_ms,
            "note": "Monitor logs for any hardware errors during ramp execution"
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
            logger.error(
                f"Hardware error in immediate control for device {channel_id} "
                f"(controller={controller_address}, channel={channel_number}, "
                f"intended_intensity={constrained_intensity}%, duty_cycle={duty_cycle}): {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to set PWM channel duty cycle. Hardware error: {e}"
            )

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
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Sets the intensity for multiple PWM channels in a single request.
    Supports both immediate and ramped changes.
    """
    results = []
    devices_to_update = []
    
    # Group immediate operations by controller address for batching
    immediate_operations = {}  # {controller_address: {channel: duty_cycle, device_info}}
    ramp_operations = []  # List of ramp operations to process individually

    # First pass: validate and group operations
    for request in requests:
        try:
            # 1. Fetch the channel device from the database
            channel_device = await device_crud.get(db, device_id=request.device_id)
            if not channel_device or channel_device.device_type != "pwm_channel":
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
                # Handle ramped request - add to individual processing list
                ramp_operations.append({
                    "request": request,
                    "channel_device": channel_device,
                    "controller_address": controller_address,
                    "channel_number": channel_number,
                    "constrained_intensity": constrained_intensity
                })
            else:
                # Handle immediate request - group by controller address
                duty_cycle = int((constrained_intensity / 100) * 65535)
                if controller_address not in immediate_operations:
                    immediate_operations[controller_address] = {}
                
                immediate_operations[controller_address][channel_number] = {
                    "duty_cycle": duty_cycle,
                    "device_id": request.device_id,
                    "channel_device": channel_device,
                    "constrained_intensity": constrained_intensity
                }

        except Exception as e:
            results.append({"device_id": request.device_id, "status": "error", "detail": str(e)})

    # Second pass: process batched immediate operations
    for controller_address, channel_operations in immediate_operations.items():
        try:
            # Prepare channel mapping for batch operation
            channel_duty_cycles = {channel: data["duty_cycle"] for channel, data in channel_operations.items()}
            
            # Perform batch hardware update
            pca9685_driver.set_multiple_channels_duty_cycle(
                address=controller_address,
                channel_duty_cycles=channel_duty_cycles
            )
            
            # Mark all devices for database update
            for channel_data in channel_operations.values():
                channel_data["channel_device"].current_value = channel_data["constrained_intensity"]
                devices_to_update.append(channel_data["channel_device"])
                
                results.append({
                    "device_id": channel_data["device_id"], 
                    "status": "success", 
                    "detail": f"Set to {channel_data['constrained_intensity']}% intensity (batched)"
                })
                
        except Exception as e:
            logger.error(
                f"Hardware error in bulk batch control for controller {controller_address}: {e}",
                exc_info=True
            )
            # Mark all channels for this controller as failed
            for channel_data in channel_operations.values():
                results.append({
                    "device_id": channel_data["device_id"], 
                    "status": "error", 
                    "detail": f"Hardware error: {str(e)}"
                })

    # Third pass: process individual ramp operations
    for ramp_op in ramp_operations:
        try:
            start_intensity = ramp_op["channel_device"].current_value or 0.0
            
            # Create a unique key for this controller/channel combination
            ramp_key = (ramp_op["controller_address"], ramp_op["channel_number"])
            
            # Cancel any existing ramp for this channel
            if ramp_key in _active_ramp_tasks:
                existing_task = _active_ramp_tasks[ramp_key]
                if not existing_task.done():
                    existing_task.cancel()
                    logger.info(f"Cancelled existing ramp for controller {ramp_op['controller_address']}, channel {ramp_op['channel_number']}")
            
            # Create and store the new ramp task
            ramp_task = asyncio.create_task(_perform_ramp(
                device_id=ramp_op["request"].device_id,
                start_intensity=start_intensity,
                end_intensity=ramp_op["constrained_intensity"],
                duration_ms=ramp_op["request"].duration_ms,
                controller_address=ramp_op["controller_address"],
                channel_number=ramp_op["channel_number"],
                curve=ramp_op["request"].curve,
                step_interval_ms=ramp_op["request"].step_interval_ms
            ))
            _active_ramp_tasks[ramp_key] = ramp_task
            
            results.append({
                "device_id": ramp_op["request"].device_id, 
                "status": "success", 
                "detail": f"Ramp initiated: {start_intensity}% → {ramp_op['constrained_intensity']}% over {ramp_op['request'].duration_ms}ms",
                "note": "Monitor logs for any hardware errors during ramp execution"
            })
            
        except Exception as e:
            results.append({"device_id": ramp_op["request"].device_id, "status": "error", "detail": str(e)})

    # Commit all database updates in a single transaction
    if devices_to_update:
        db.add_all(devices_to_update)
        await db.commit()

    return results

@router.get("/{channel_id}/state", response_model=float, summary="Get Current PWM Channel State")
async def get_pwm_channel_state(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Gets the last known intensity for a configured PWM channel device from the database.
    """
    channel_device = await device_crud.get(db, device_id=channel_id)
    if not channel_device or channel_device.device_type != "pwm_channel":
        raise HTTPException(status_code=404, detail="PWM Channel device not found.")

    return channel_device.current_value

@router.get("/{channel_id}/live-state", response_model=float, summary="Get Live Hardware State")
async def get_pwm_channel_live_state(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Gets the current intensity directly from the hardware and updates the database.
    This provides a guaranteed, real-time value for diagnostics and state synchronization.
    """
    # 1. Fetch the channel device from the database
    channel_device = await device_crud.get(db, device_id=channel_id)
    if not channel_device or channel_device.device_type != "pwm_channel":
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

    # 4. Read the current duty cycle from the hardware
    try:
        duty_cycle = pca9685_driver.get_current_duty_cycle(controller_address, channel_number)
    except (ValueError, IOError) as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Failed to read PWM channel duty cycle from hardware: {str(e)}"
        )

    # 5. Convert 16-bit duty cycle (0-65535) to intensity percentage (0.0-100.0)
    intensity_percentage = (duty_cycle / 65535) * 100.0

    # 6. Update the database with the live value to re-synchronize state
    channel_device.current_value = intensity_percentage
    db.add(channel_device)
    await db.commit()

    return intensity_percentage

@router.get("/{channel_id}/hw_state", response_model=float, summary="Get Hardware PWM State")
async def get_pwm_channel_hw_state(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Gets the current intensity directly from the hardware without updating the database.
    This provides a read-only hardware state for diagnostics and monitoring.
    """
    # 1. Fetch the channel device from the database
    channel_device = await device_crud.get(db, device_id=channel_id)
    if not channel_device or channel_device.device_type != "pwm_channel":
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

    # 4. Read the current duty cycle from the hardware
    try:
        duty_cycle = pca9685_driver.get_current_duty_cycle(controller_address, channel_number)
    except (ValueError, IOError) as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Failed to read PWM channel duty cycle from hardware: {str(e)}"
        )

    # 5. Convert 16-bit duty cycle (0-65535) to intensity percentage (0.0-100.0)
    intensity_percentage = (duty_cycle / 65535) * 100.0

    return intensity_percentage

@router.get("", response_model=List[device_schema.Device], summary="List All Registered PWM Channels")
async def list_all_pwm_channels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Retrieves a list of all devices configured with the 'pwm_channel' role across all controllers.
    """
    channels = await device_crud.get_multi(db, device_type="pwm_channel")
    return channels

@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Single PWM Channel")
async def delete_pwm_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_or_service)
):
    """
    Deletes a single registered PWM channel device by its database ID.
    """
    # First, fetch the device to ensure it exists and is a PWM channel
    device_to_delete = await device_crud.get(db, device_id=channel_id)

    if not device_to_delete or device_to_delete.device_type != "pwm_channel":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PWM Channel with ID {channel_id} not found."
        )

    # If it exists and is the correct type, remove it
    await device_crud.remove(db, device_id=channel_id)

    # Return a 204 No Content response to indicate success
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{channel_id}", response_model=device_schema.Device, summary="Get Single Channel Details")
async def get_channel_by_id(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_or_service)
):
    """
    Retrieves the configuration of a single PWM channel by its database ID.
    """
    channel = await device_crud.get(db, device_id=channel_id)
    if not channel or channel.device_type != "pwm_channel":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PWM Channel with ID {channel_id} not found."
        )
    return channel

@router.patch("/{channel_id}", response_model=device_schema.Device, summary="Update a Channel's Properties")
async def update_channel(
    channel_id: int,
    update_data: PWMChannelUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_or_service)
):
    """
    Updates the properties (e.g., name, role, min/max values) of a registered PWM channel.
    """
    channel = await device_crud.get(db, device_id=channel_id)
    if not channel or channel.device_type != "pwm_channel":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PWM Channel with ID {channel_id} not found."
        )

    device_update_data = device_schema.DeviceUpdate(**update_data.model_dump(exclude_unset=True))
    updated_device = await device_crud.update(db, db_obj=channel, obj_in=device_update_data)
    return updated_device

@router.post("/debug/pca_write", status_code=status.HTTP_200_OK, summary="Debug PCA9685 Hardware Write")
async def debug_pca_write(
    address: int,
    channel: int,
    duty_cycle: int,
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Temporary debug endpoint to perform a single hardware write to PCA9685.
    For real-time diagnostics only.
    """
    logger.info(f"DEBUG_PCA_WRITE: Starting debug hardware write - I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
    
    try:
        # Validate inputs
        if not 0 <= channel <= 15:
            raise HTTPException(status_code=400, detail=f"Channel must be between 0 and 15 inclusive, got {channel}")
        if not 0 <= duty_cycle <= 65535:
            raise HTTPException(status_code=400, detail=f"Duty cycle must be between 0 and 65535 inclusive, got {duty_cycle}")
        
        # Perform the hardware write
        pca9685_driver.set_channel_duty_cycle(address=address, channel=channel, duty_cycle=duty_cycle)
        
        logger.info(f"DEBUG_PCA_WRITE_SUCCESS: Hardware write completed - I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}")
        
        return {
            "status": "success",
            "message": f"Hardware write completed successfully",
            "address": f"0x{address:02X}",
            "channel": channel,
            "duty_cycle": duty_cycle,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error(f"DEBUG_PCA_WRITE_ERROR: Hardware write failed - I2C=0x{address:02X}, Channel={channel}, DutyCycle={duty_cycle}, Error={type(e).__name__}: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Hardware write failed: {type(e).__name__}: {e}"
        ) 