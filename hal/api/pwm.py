from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.crud import device as device_crud
from shared.schemas.enums import DeviceRole
from shared.schemas.user import User
from core.api.deps import get_current_user

from ..drivers import pca9685_driver
from .schemas import PWMControlRequest

router = APIRouter(prefix="/pwm", tags=["PWM Control"])

@router.post("/set-duty-cycle", status_code=status.HTTP_200_OK)
async def set_pwm_channel_duty_cycle(
    request: PWMControlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sets the intensity (duty cycle) for a configured PWM channel device.
    """
    # 1. Fetch the channel device from the database
    channel_device = await device_crud.get(db, device_id=request.device_id)
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

@router.get("/{device_id}/state", response_model=float, summary="Get Current PWM Channel State")
async def get_pwm_channel_state(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Gets the last known intensity for a configured PWM channel device from the database.
    """
    channel_device = await device_crud.get(db, device_id=device_id)
    if not channel_device or channel_device.role != DeviceRole.PWM_CHANNEL.value:
        raise HTTPException(status_code=404, detail="PWM Channel device not found.")

    return channel_device.current_value 