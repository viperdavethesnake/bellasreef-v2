from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from shared.db.database import get_db
from shared.crud import device as device_crud
from shared.schemas import device as device_schema
from shared.schemas.enums import DeviceRole
from shared.schemas.user import User
from core.api.deps import get_current_user

from ..drivers import pca9685_driver
from .schemas import PCA9685DiscoveryResult, PCA9685RegistrationRequest, PWMChannelRegistrationRequest

router = APIRouter(prefix="/controllers", tags=["Controllers"])

@router.get("/discover", response_model=List[PCA9685DiscoveryResult])
async def discover_pca9685_controller(
    current_user: User = Depends(get_current_user)
):
    """
    Scans the I2C bus for all PCA9685 devices across a range of addresses.
    """
    # Define the range of I2C addresses to scan (0x40 to 0x77)
    # This covers the standard 7-bit I2C address range for PCA9685 devices
    i2c_addresses = list(range(0x40, 0x78))  # 0x40 to 0x77 inclusive
    
    discovered_devices = []
    
    # Scan each address in the range
    for address in i2c_addresses:
        is_found = pca9685_driver.check_board(address)
        if is_found:
            message = f"PCA9685 controller found at address {hex(address)}."
            discovered_devices.append(
                PCA9685DiscoveryResult(
                    address=address, 
                    is_found=True, 
                    message=message
                )
            )
    
    # If no devices found, add a single result indicating no devices
    if not discovered_devices:
        discovered_devices.append(
            PCA9685DiscoveryResult(
                address=0x40,  # Default address for reference
                is_found=False, 
                message="No PCA9685 controllers found on the I2C bus."
            )
        )
    
    return discovered_devices

@router.post("", response_model=device_schema.Device, status_code=status.HTTP_201_CREATED)
async def create_pca9685_controller(
    request: PCA9685RegistrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    if existing_device and existing_device.role == DeviceRole.CONTROLLER.value and existing_device.device_type == "pca9685":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A PCA9685 controller at address {hex(request.address)} is already registered."
        )

    # Create the device entry in the database
    device_data = device_schema.DeviceCreate(
        name=request.name,
        device_type="pca9685",
        address=str(request.address), # Store address as a string
        role=DeviceRole.CONTROLLER,
        config={"frequency": request.frequency}
    )
    
    new_device = await device_crud.create(db, obj_in=device_data)
    return new_device

@router.get("", response_model=List[device_schema.Device])
async def list_registered_controllers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a list of all registered PCA9685 controller devices.
    """
    controllers = await device_crud.get_multi(
        db, role=DeviceRole.CONTROLLER.value
    )
    # Filter to only PCA9685 controllers
    return [controller for controller in controllers if controller.device_type == "pca9685"]

@router.post("/{controller_id}/channels", response_model=device_schema.Device, status_code=status.HTTP_201_CREATED)
async def register_pwm_channel(
    controller_id: int,
    request: PWMChannelRegistrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registers an individual PWM channel as a new 'child' device, linked to a parent PCA9685 controller.
    """
    # 1. Verify the parent controller exists and is a PCA9685 controller
    parent_controller = await device_crud.get(db, device_id=controller_id)
    if not parent_controller or parent_controller.role != DeviceRole.CONTROLLER.value or parent_controller.device_type != "pca9685":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent controller with ID {controller_id} not found or is not a PCA9685 controller."
        )

    # 2. Check if this channel is already registered for this parent
    for child in parent_controller.children:
        if child.config and child.config.get("channel_number") == request.channel_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Channel {request.channel_number} is already registered for controller ID {controller_id}."
            )

    # 3. Create the new channel device entry
    device_data = device_schema.DeviceCreate(
        name=request.name,
        device_type="pwm_channel",
        # The address for a channel is a composite of parent and channel for uniqueness
        address=f"pca9685_{controller_id}_ch{request.channel_number}",
        role=request.role,
        parent_device_id=controller_id,
        # Store hardware-specific info in the config JSON field
        config={"channel_number": request.channel_number},
        min_value=request.min_value,
        max_value=request.max_value
    )
    
    new_device = await device_crud.create(db, obj_in=device_data)
    return new_device

@router.get("/{controller_id}/channels", response_model=List[device_schema.Device])
async def get_configured_channels(
    controller_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a list of all PWM channels that have been configured for a specific PCA9685 controller.
    """
    # Verify the parent controller exists
    parent_controller = await device_crud.get(db, device_id=controller_id)
    if not parent_controller or parent_controller.role != DeviceRole.CONTROLLER.value or parent_controller.device_type != "pca9685":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent controller with ID {controller_id} not found or is not a PCA9685 controller."
        )

    # The 'children' relationship we defined in the model makes this easy
    return parent_controller.children

@router.delete("/{controller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pca9685_controller(
    controller_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a registered PCA9685 controller and all its associated PWM channels.
    """
    # Retrieve the device to verify it exists and is a PCA9685 controller
    controller = await device_crud.get(db, device_id=controller_id)
    if not controller or controller.role != DeviceRole.CONTROLLER.value or controller.device_type != "pca9685":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PCA9685 controller with ID {controller_id} not found."
        )
    
    # Delete the controller (cascading delete will handle child channels)
    await device_crud.remove(db, device_id=controller_id)
    
    return None 