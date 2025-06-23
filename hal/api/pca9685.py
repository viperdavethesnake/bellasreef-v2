from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from shared.db.database import get_db
from shared.crud import device as device_crud
from shared.schemas import device as device_schema
from shared.schemas.enums import DeviceRole

from ..drivers import pca9685_driver
from .schemas import PCA9685DiscoveryResult, PCA9685RegistrationRequest, PWMChannelRegistrationRequest

router = APIRouter(prefix="/pca9685", tags=["PCA9685 Controller"])

@router.get("/discover", response_model=PCA9685DiscoveryResult)
async def discover_pca9685_controller(address: int = 0x40):
    """
    Scans the I2C bus for a PCA9685 device at a given address.
    """
    is_found = pca9685_driver.check_board(address)
    message = "PCA9685 controller found successfully." if is_found else "PCA9685 controller not found at the specified address."
    
    return PCA9685DiscoveryResult(address=address, is_found=is_found, message=message)

@router.post("/register", response_model=device_schema.Device, status_code=status.HTTP_201_CREATED)
async def register_pca9685_controller(
    request: PCA9685RegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new PCA9685 controller as a 'parent' device in the system.
    """
    # Verify the device actually exists before registering
    if not pca9685_driver.check_board(request.address):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot register controller: No PCA9685 device found at address {hex(request.address)}."
        )

    # Check if a controller with this address is already registered
    existing_device = await device_crud.get_by_address(db, str(request.address))
    if existing_device and existing_device.role == DeviceRole.PCA9685_CONTROLLER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A PCA9685 controller at address {hex(request.address)} is already registered."
        )

    # Create the device entry in the database
    device_data = device_schema.DeviceCreate(
        name=request.name,
        device_type="pca9685",
        address=str(request.address), # Store address as a string
        role=DeviceRole.PCA9685_CONTROLLER,
        config={"frequency": request.frequency}
    )
    
    new_device = await device_crud.create(db, obj_in=device_data)
    return new_device

@router.post("/channel/register", response_model=device_schema.Device, status_code=status.HTTP_201_CREATED)
async def register_pwm_channel(
    request: PWMChannelRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers an individual PWM channel as a new 'child' device, linked to a parent PCA9685 controller.
    """
    # 1. Verify the parent controller exists and is a PCA9685 controller
    parent_controller = await device_crud.get(db, device_id=request.parent_controller_id)
    if not parent_controller or parent_controller.role != DeviceRole.PCA9685_CONTROLLER.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent controller with ID {request.parent_controller_id} not found or is not a PCA9685 controller."
        )

    # 2. Check if this channel is already registered for this parent
    for child in parent_controller.children:
        if child.config and child.config.get("channel_number") == request.channel_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Channel {request.channel_number} is already registered for controller ID {request.parent_controller_id}."
            )

    # 3. Create the new channel device entry
    device_data = device_schema.DeviceCreate(
        name=request.name,
        device_type="pwm_channel",
        # The address for a channel is a composite of parent and channel for uniqueness
        address=f"pca9685_{request.parent_controller_id}_ch{request.channel_number}",
        role=request.role,
        parent_device_id=request.parent_controller_id,
        # Store hardware-specific info in the config JSON field
        config={"channel_number": request.channel_number},
        min_value=request.min_value,
        max_value=request.max_value
    )
    
    new_device = await device_crud.create(db, obj_in=device_data)
    return new_device

@router.get("/{controller_id}/channels", response_model=List[device_schema.Device])
async def get_configured_channels(controller_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a list of all PWM channels that have been configured for a specific PCA9685 controller.
    """
    # Verify the parent controller exists
    parent_controller = await device_crud.get(db, device_id=controller_id)
    if not parent_controller or parent_controller.role != DeviceRole.PCA9685_CONTROLLER.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent controller with ID {controller_id} not found or is not a PCA9685 controller."
        )

    # The 'children' relationship we defined in the model makes this easy
    return parent_controller.children 