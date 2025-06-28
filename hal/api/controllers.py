from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List
import time

from shared.db.database import get_db
from shared.crud import device as device_crud
from shared.schemas import device as device_schema
from shared.db.models import Device as DeviceModel
from shared.schemas.enums import DeviceRole
from shared.schemas.user import User
from shared.api.deps import get_current_user_or_service

from ..drivers import pca9685_driver
from ..drivers.pca9685_driver import reconnect_controller, get_manager_status
from .schemas import PCA9685DiscoveryResult, PCA9685RegistrationRequest, PWMChannelRegistrationRequest, PWMFrequencyUpdateRequest, ControllerUpdateRequest

router = APIRouter(prefix="/controllers", tags=["Controllers"])

@router.get("/discover", response_model=List[PCA9685DiscoveryResult])
async def discover_pca9685_controller(
    current_user: User = Depends(get_current_user_or_service)
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
    current_user: User = Depends(get_current_user_or_service)
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
    current_user: User = Depends(get_current_user_or_service)
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
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Registers an individual PWM channel as a new 'child' device, linked to a parent PCA9685 controller.
    """
    # 1. Verify the parent controller exists and is a PCA9685 controller
    # Explicitly load the parent controller with its children to prevent lazy loading errors
    query = select(DeviceModel).options(selectinload(DeviceModel.children)).filter(DeviceModel.id == controller_id)
    result = await db.execute(query)
    parent_controller = result.scalar_one_or_none()
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
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Retrieves a list of all PWM channels that have been configured for a specific PCA9685 controller.
    """
    # Verify the parent controller exists
    # Explicitly load the parent controller with its children to prevent lazy loading errors
    query = select(DeviceModel).options(selectinload(DeviceModel.children)).filter(DeviceModel.id == controller_id)
    result = await db.execute(query)
    parent_controller = result.scalar_one_or_none()
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
    current_user: User = Depends(get_current_user_or_service)
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

@router.patch("/{controller_id}/frequency", response_model=device_schema.Device)
async def update_pwm_frequency(
    controller_id: int,
    request: PWMFrequencyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Updates the PWM frequency of a registered PCA9685 controller.
    """
    # Retrieve the controller device from the database
    controller = await device_crud.get(db, device_id=controller_id)
    if not controller or controller.role != DeviceRole.CONTROLLER.value or controller.device_type != "pca9685":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PCA9685 controller with ID {controller_id} not found."
        )
    
    # Apply the frequency change to the physical hardware
    try:
        controller_address = int(controller.address)
        pca9685_driver.set_frequency(controller_address, request.frequency)
    except (ValueError, IOError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to update PWM frequency on hardware: {str(e)}"
        )
    
    # Update the config dictionary in the device's database record
    if not controller.config:
        controller.config = {}
    controller.config["frequency"] = request.frequency
    
    # Save the changes to the database
    db.add(controller)
    await db.commit()
    await db.refresh(controller)
    
    return controller

@router.get("/{controller_id}", response_model=device_schema.Device, summary="Get Single Controller Details")
async def get_controller_by_id(
    controller_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_or_service)
):
    """
    Retrieves the details of a single registered PCA9685 controller by its database ID.
    """
    controller = await device_crud.get(db, device_id=controller_id)
    if not controller or controller.role != "controller":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with ID {controller_id} not found."
        )
    return controller

@router.patch("/{controller_id}", response_model=device_schema.Device, summary="Update a Controller's Properties")
async def update_controller(
    controller_id: int,
    update_data: ControllerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_or_service)
):
    """
    Updates the properties (e.g., name) of a registered PCA9685 controller.
    """
    controller = await device_crud.get(db, device_id=controller_id)
    if not controller or controller.role != "controller":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with ID {controller_id} not found."
        )

    device_update_data = device_schema.DeviceUpdate(**update_data.model_dump(exclude_unset=True))
    updated_device = await device_crud.update(db, db_obj=controller, obj_in=device_update_data)
    return updated_device

@router.post("/{controller_id}/reconnect", status_code=status.HTTP_200_OK)
async def reconnect_controller_endpoint(
    controller_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Attempts to reconnect to a PCA9685 controller that may have failed.
    """
    # Retrieve the controller device from the database
    controller = await device_crud.get(db, device_id=controller_id)
    if not controller or controller.role != DeviceRole.CONTROLLER.value or controller.device_type != "pca9685":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PCA9685 controller with ID {controller_id} not found."
        )
    
    # Attempt to reconnect to the hardware
    controller_address = int(controller.address)
    success = reconnect_controller(controller_address)
    
    if success:
        return {
            "message": f"Successfully reconnected to controller at address {hex(controller_address)}",
            "controller_id": controller_id,
            "address": controller_address,
            "status": "reconnected"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reconnect to controller at address {hex(controller_address)}"
        )

@router.get("/hardware-manager/status", status_code=status.HTTP_200_OK)
async def get_hardware_manager_status(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get the current status of the hardware manager for debugging.
    """
    status = get_manager_status()
    return {
        "hardware_manager_status": status,
        "timestamp": time.time()
    } 