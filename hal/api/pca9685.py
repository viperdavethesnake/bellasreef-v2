from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.crud import device as device_crud
from shared.schemas import device as device_schema
from shared.schemas.enums import DeviceRole

from ..drivers import pca9685_driver
from .schemas import PCA9685DiscoveryResult, PCA9685RegistrationRequest

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