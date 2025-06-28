"""
SmartOutlet API Routes

This module defines FastAPI routes for smart outlet operations, including
creation, update, control, and discovery of smart outlets. All endpoints
are documented for OpenAPI/Swagger UI.
"""

from uuid import uuid4
from typing import List, Optional
import asyncio
from datetime import datetime
import pytz

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pyvesync import VeSync

from shared.db.database import async_session
from shared.utils.logger import get_logger
from .manager import SmartOutletManager
from shared.db.models import SmartOutlet, VeSyncAccount
from .schemas import (
    SmartOutletCreate, SmartOutletRead, SmartOutletState, SmartOutletUpdate,
    VeSyncDiscoveryRequest, DiscoveredDevice, DiscoveryTaskResponse, DiscoveryResults,
    VeSyncAccountCreate, VeSyncAccountRead, DiscoveredVeSyncDevice, VeSyncDeviceCreate, SmartOutletWithState
)
from .exceptions import OutletNotFoundError, OutletConnectionError, OutletAuthenticationError
from .handlers import register_exception_handlers
from .discovery_service import DiscoveryService
from shared.core.config import settings
from .crypto_utils import encrypt_vesync_password, decrypt_vesync_password
from .services.vesync_device_service import vesync_device_service
from shared.api.deps import get_current_user_or_service
from shared.schemas.user import User

router = APIRouter()

# Global discovery service instance
discovery_service = DiscoveryService()


async def get_smart_outlet_manager() -> SmartOutletManager:
    """
    Dependency to provide a SmartOutletManager instance.

    Returns:
        SmartOutletManager: The manager instance
    """
    logger = get_logger(__name__)
    return SmartOutletManager(async_session, logger)


async def get_db_session() -> AsyncSession:
    """
    Dependency to provide a database session.
    
    Returns:
        AsyncSession: Database session instance
    """
    async with async_session() as session:
        yield session


@router.post(
    "/outlets/",
    response_model=SmartOutletRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new smart outlet",
    description="Creates a new smart outlet record in the database and registers it with the manager.",
    tags=["Smart Outlets"]
)
async def create_outlet(
    outlet_data: SmartOutletCreate,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Create a new smart outlet.

    Args:
        outlet_data: Smart outlet creation data
        manager: SmartOutletManager instance
        session: Database session
        current_user: Current authenticated user or service

    Returns:
        SmartOutletRead: Created outlet data

    Raises:
        HTTPException: If outlet with same driver_type and driver_device_id already exists
    """
    # Check for uniqueness constraint
    existing_outlet = await session.execute(
        select(SmartOutlet).where(
            SmartOutlet.driver_type == outlet_data.driver_type.value,
            SmartOutlet.driver_device_id == outlet_data.driver_device_id
        )
    )
    
    if existing_outlet.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Outlet with driver_type '{outlet_data.driver_type.value}' and driver_device_id '{outlet_data.driver_device_id}' already exists"
        )
    
    # Create new outlet
    outlet = SmartOutlet(
        id=uuid4(),
        driver_type=outlet_data.driver_type.value,
        driver_device_id=outlet_data.driver_device_id,
        name=outlet_data.name,
        nickname=outlet_data.nickname,
        ip_address=outlet_data.ip_address,
        auth_info=outlet_data.auth_info,
        location=outlet_data.location,
        role=outlet_data.role.value,
        enabled=outlet_data.enabled,
        poller_enabled=outlet_data.poller_enabled,
        scheduler_enabled=outlet_data.scheduler_enabled
    )
    
    session.add(outlet)
    await session.commit()
    await session.refresh(outlet)
    
    # Register outlet with manager
    try:
        await manager.register_outlet_from_db(outlet.id)
    except Exception as e:
        # Log error but don't fail the creation
        pass
    
    return SmartOutletRead.model_validate(outlet)


@router.get(
    "/outlets/",
    response_model=List[SmartOutletRead],
    summary="List all smart outlets",
    description="Retrieves a list of all smart outlets, optionally including disabled ones.",
    tags=["Smart Outlets"]
)
async def list_outlets(
    include_disabled: bool = Query(False, description="Include disabled outlets"),
    driver_type: Optional[str] = Query(None, description="Filter by driver type (e.g., kasa, vesync)"),
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    List all smart outlets.

    Args:
        include_disabled: Whether to include disabled outlets
        driver_type: Optional driver type to filter by
        manager: SmartOutletManager instance
        current_user: Current authenticated user or service

    Returns:
        List[SmartOutletRead]: List of outlet data
    """
    outlets = await manager.get_all_outlets(
        include_disabled=include_disabled, driver_type=driver_type
    )
    return [SmartOutletRead.model_validate(outlet) for outlet in outlets]


@router.delete(
    "/outlets/{outlet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a smart outlet",
    tags=["Smart Outlets"],
)
async def delete_outlet(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    current_user: User = Depends(get_current_user_or_service),
):
    """
    Delete a smart outlet from the system.
    """
    try:
        await manager.delete_outlet(outlet_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except OutletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/outlets/{outlet_id}",
    response_model=SmartOutletRead,
    status_code=status.HTTP_200_OK,
    summary="Update a smart outlet",
    description="Updates the configuration of an existing smart outlet.",
    tags=["Smart Outlets"]
)
async def update_outlet(
    outlet_id: str,
    update_data: SmartOutletUpdate,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Update an existing smart outlet configuration.

    Args:
        outlet_id: The ID of the outlet to update
        update_data: Update data containing allowed fields
        manager: SmartOutletManager instance
        current_user: Current authenticated user or service

    Returns:
        SmartOutletRead: Updated outlet data
    """
    return await manager.update_outlet(outlet_id, update_data)


@router.get(
    "/outlets/{outlet_id}/state",
    response_model=SmartOutletState,
    summary="Get smart outlet state",
    description="Retrieves the current state and telemetry of a smart outlet.",
    tags=["State"]
)
async def get_outlet_state(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get the current state of a smart outlet.

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        current_user: Current authenticated user or service

    Returns:
        SmartOutletState: Current outlet state
    """
    return await manager.get_outlet_status(outlet_id)


@router.post(
    "/outlets/{outlet_id}/turn_on",
    status_code=status.HTTP_200_OK,
    summary="Turn on smart outlet",
    description="Activates the specified smart outlet using its configured driver.",
    tags=["Control"]
)
async def turn_on_outlet(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Turn on a smart outlet.

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        current_user: Current authenticated user or service

    Returns:
        dict: Success response
    """
    success = await manager.turn_on_outlet(outlet_id)
    if success:
        return {"message": f"Successfully turned on outlet {outlet_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to turn on outlet {outlet_id}"
        )


@router.post(
    "/outlets/{outlet_id}/turn_off",
    status_code=status.HTTP_200_OK,
    summary="Turn off smart outlet",
    description="Deactivates the specified smart outlet using its configured driver.",
    tags=["Control"]
)
async def turn_off_outlet(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Turn off a smart outlet.

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        current_user: Current authenticated user or service

    Returns:
        dict: Success response
    """
    success = await manager.turn_off_outlet(outlet_id)
    if success:
        return {"message": f"Successfully turned off outlet {outlet_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to turn off outlet {outlet_id}"
        )


@router.post(
    "/outlets/{outlet_id}/toggle",
    response_model=SmartOutletState,
    summary="Toggle smart outlet",
    description="Toggles the state of the specified smart outlet (on/off).",
    tags=["Control"]
)
async def toggle_outlet(
    outlet_id: str,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Toggle a smart outlet.

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance
        current_user: Current authenticated user or service

    Returns:
        SmartOutletState: Current outlet state after toggle
    """
    return await manager.toggle_outlet(outlet_id)


# Discovery Endpoints

@router.post(
    "/outlets/discover/local",
    response_model=DiscoveryTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start local device discovery",
    description="Initiates asynchronous discovery of Shelly and Kasa devices on the local network.",
    tags=["Discovery"]
)
async def start_local_discovery(
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Start local device discovery.

    Args:
        current_user: Current authenticated user or service

    Returns:
        DiscoveryTaskResponse: Discovery task information
    """
    task_id = await discovery_service.run_local_discovery()
    return DiscoveryTaskResponse(
        task_id=task_id
    )


@router.get(
    "/outlets/discover/local/{task_id}/results",
    response_model=DiscoveryResults,
    summary="Get local discovery results",
    description="Retrieves the results of a local device discovery task by task ID.",
    tags=["Discovery"]
)
async def get_local_discovery_results(task_id: str):
    """
    Get results from a local discovery task.
    """
    result_data = await discovery_service.get_discovery_results(task_id)

    if not result_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery task {task_id} not found",
        )

    return DiscoveryResults(
        task_id=task_id,
        status=result_data.get("status", "unknown"),
        created_at=result_data.get("created_at"),
        completed_at=result_data.get("completed_at"),
        results=[DiscoveredDevice(**dev) for dev in result_data.get("results", [])],
        error=result_data.get("error"),
    )


@router.post(
    "/outlets/discover/cloud/vesync",
    response_model=List[DiscoveredDevice],
    summary="Discover VeSync cloud devices",
    description="Discovers VeSync smart outlets using provided cloud credentials.",
    tags=["Discovery"]
)
async def discover_vesync_devices(
    request: VeSyncDiscoveryRequest,
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Discover VeSync cloud devices.

    Args:
        request: VeSync discovery request with credentials
        current_user: Current authenticated user or service

    Returns:
        List[DiscoveredDevice]: List of discovered devices
    """
    try:
        # Create VeSync manager with provided credentials
        manager = VeSync(
            request.email,
            request.password.get_secret_value(),
            time_zone=request.time_zone or "America/New_York"
        )
        
        # Login to VeSync
        if not manager.login():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid VeSync credentials"
            )
        
        # Update device list
        if not manager.update():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update device list from VeSync cloud"
            )
        
        # Get all devices
        devices = []
        
        # Process outlets
        if hasattr(manager, 'outlets') and isinstance(manager.outlets, list):
            for outlet in manager.outlets:
                if hasattr(outlet, 'device_name') and hasattr(outlet, 'cid'):
                    devices.append(DiscoveredDevice(
                        device_id=outlet.cid,
                        device_name=outlet.device_name,
                        device_type="vesync",
                        ip_address="",  # Cloud devices don't have local IP
                        capabilities=["on_off", "power_monitoring"] if hasattr(outlet, 'power') else ["on_off"]
                    ))
        
        # Process switches
        if hasattr(manager, 'switches') and isinstance(manager.switches, list):
            for switch in manager.switches:
                if hasattr(switch, 'device_name') and hasattr(switch, 'cid'):
                    devices.append(DiscoveredDevice(
                        device_id=switch.cid,
                        device_name=switch.device_name,
                        device_type="vesync",
                        ip_address="",  # Cloud devices don't have local IP
                        capabilities=["on_off", "power_monitoring"] if hasattr(switch, 'power') else ["on_off"]
                    ))
        
        return devices
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"VeSync discovery failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"VeSync discovery failed: {str(e)}"
        )


# =============================================================================
# VeSync Account Management Router
# =============================================================================

async def get_vesync_account_or_404(account_id: int, db: AsyncSession) -> VeSyncAccount:
    """Helper to fetch a VeSync account by ID or raise HTTPException 404."""
    result = await db.execute(select(VeSyncAccount).filter(VeSyncAccount.id == account_id))
    db_account = result.scalars().first()
    if db_account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VeSync account not found")
    return db_account


vesync_router = APIRouter(
    tags=["VeSync Accounts"],
    responses={404: {"description": "Not found"}},
)


@vesync_router.post("/", response_model=VeSyncAccountRead, status_code=status.HTTP_201_CREATED)
async def create_vesync_account(
    account: VeSyncAccountCreate, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Create a new VeSync account.
    """
    # Check if an account with this email already exists
    existing_account_result = await db.execute(
        select(VeSyncAccount).filter(VeSyncAccount.email == account.email)
    )
    if existing_account_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Encrypt the password before storing
    encrypted_password = encrypt_vesync_password(account.password.get_secret_value())
    if not encrypted_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt password.",
        )

    db_account = VeSyncAccount(
        email=account.email,
        password_encrypted=encrypted_password.encode(),
        is_active=account.is_active,
        time_zone=account.time_zone
    )

    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account


@vesync_router.get("/", response_model=List[VeSyncAccountRead])
async def read_vesync_accounts(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Retrieve all VeSync accounts.
    """
    result = await db.execute(select(VeSyncAccount).offset(skip).limit(limit))
    accounts = result.scalars().all()
    return accounts


@vesync_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vesync_account(
    account_id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Delete a VeSync account.
    """
    db_account = await get_vesync_account_or_404(account_id, db)
    await db.delete(db_account)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@vesync_router.post("/{account_id}/verify", response_model=VeSyncAccountRead)
async def verify_vesync_account(
    account_id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Verify the credentials for a VeSync account by attempting to log in.
    """
    db_account = await get_vesync_account_or_404(account_id, db)

    password = decrypt_vesync_password(db_account.password_encrypted.decode())
    if not password:
        db_account.last_sync_status = "Decryption Failed"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not decrypt password for verification.",
        )

    manager = VeSync(db_account.email, password, time_zone=db_account.time_zone)
    login_success = False
    error_detail = None

    try:
        # This is a synchronous call, run it in a thread to avoid blocking the event loop
        login_success = await asyncio.to_thread(manager.login)
        if not login_success:
             error_detail = manager.error_msg or "Unknown login error"
    except Exception as e:
        # Catch any exceptions during login and check manager.error_msg first
        error_detail = manager.error_msg or f"Login failed: {str(e)}"

    # Update the account status in the database
    db_account.last_synced_at = datetime.now(pytz.utc)
    if login_success:
        db_account.last_sync_status = "Success"
    else:
        db_account.last_sync_status = f"Login Failed: {error_detail}"

    await db.commit()
    await db.refresh(db_account)
    return db_account


# =============================================================================
# VeSync Device Management Endpoints
# =============================================================================

@vesync_router.get("/{account_id}/devices/discover", response_model=List[DiscoveredVeSyncDevice])
async def discover_vesync_devices_for_account(
    account_id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Discover all devices available for a VeSync account that are not yet managed locally.
    """
    # Get the VeSync account
    account = await get_vesync_account_or_404(account_id, db)
    
    # Discover all devices from VeSync cloud
    cloud_devices = await vesync_device_service.discover_devices(account)
    
    # Get list of already managed devices for this account
    managed_devices_result = await db.execute(
        select(SmartOutlet).filter(
            SmartOutlet.vesync_account_id == account_id,
            SmartOutlet.driver_type == "vesync"
        )
    )
    managed_devices = managed_devices_result.scalars().all()
    managed_device_ids = {device.driver_device_id for device in managed_devices}
    
    # Return only devices not already managed
    unmanaged_devices = [
        device for device in cloud_devices 
        if device.vesync_device_id not in managed_device_ids
    ]
    
    return unmanaged_devices


@vesync_router.post("/{account_id}/devices", response_model=SmartOutletRead, status_code=status.HTTP_201_CREATED)
async def add_vesync_device(
    account_id: int, 
    device_data: VeSyncDeviceCreate, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Add a discovered VeSync device to the local management system.
    """
    # Get the VeSync account
    account = await get_vesync_account_or_404(account_id, db)
    
    # Verify the device exists in VeSync cloud
    cloud_devices = await vesync_device_service.discover_devices(account)
    device_exists = any(device.vesync_device_id == device_data.vesync_device_id for device in cloud_devices)
    
    if not device_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_data.vesync_device_id} not found in VeSync account"
        )
    
    # Check if device is already managed
    existing_device = await db.execute(
        select(SmartOutlet).filter(
            SmartOutlet.driver_device_id == device_data.vesync_device_id,
            SmartOutlet.driver_type == "vesync"
        )
    )
    if existing_device.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {device_data.vesync_device_id} is already managed"
        )
    
    # Decrypt the password from the account object
    decrypted_password = decrypt_vesync_password(account.password_encrypted.decode())
    if not decrypted_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt password to create device auth_info.",
        )

    # Create the auth_info dictionary
    auth_info_data = {
        "email": account.email,
        "password": decrypted_password,
        "time_zone": account.time_zone
    }

    # Create new SmartOutlet record
    outlet = SmartOutlet(
        id=uuid4(),
        driver_type="vesync",
        driver_device_id=device_data.vesync_device_id,
        vesync_account_id=account_id,
        name=device_data.name,
        nickname=device_data.nickname,
        ip_address="cloud",  # VeSync devices are cloud-based
        auth_info=auth_info_data,
        location=device_data.location,
        role=device_data.role.value,
        enabled=True,
        poller_enabled=True,
        scheduler_enabled=True
    )
    
    db.add(outlet)
    await db.commit()
    await db.refresh(outlet)
    
    return SmartOutletRead.model_validate(outlet)


@vesync_router.get("/{account_id}/devices", response_model=List[SmartOutletRead])
async def list_vesync_devices(
    account_id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    List all devices managed for a specific VeSync account.
    """
    # Verify the account exists
    await get_vesync_account_or_404(account_id, db)
    
    # Get all devices for this account
    result = await db.execute(
        select(SmartOutlet).filter(
            SmartOutlet.vesync_account_id == account_id,
            SmartOutlet.driver_type == "vesync"
        )
    )
    devices = result.scalars().all()
    return [SmartOutletRead.model_validate(device) for device in devices]


@vesync_router.get("/{account_id}/devices/{device_id}", response_model=SmartOutletWithState)
async def get_vesync_device_state(
    account_id: int, 
    device_id: str, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Get the current state and details of a specific VeSync device.
    """
    # Get the VeSync account
    account = await get_vesync_account_or_404(account_id, db)
    
    # Get the device from database
    device_result = await db.execute(
        select(SmartOutlet).filter(
            SmartOutlet.id == device_id,
            SmartOutlet.vesync_account_id == account_id,
            SmartOutlet.driver_type == "vesync"
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VeSync device not found"
        )
    
    # Get real-time state from VeSync
    try:
        state = await vesync_device_service.get_device_state(account, device.driver_device_id)
        
        # Combine database data with real-time state
        device_data = SmartOutletRead.model_validate(device).model_dump()
        device_data.update(state)
        
        return SmartOutletWithState(**device_data)
        
    except (OutletAuthenticationError, OutletConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@vesync_router.post("/{account_id}/devices/{device_id}/turn_on", response_model=SmartOutletWithState)
async def turn_on_vesync_device(
    account_id: int, 
    device_id: str, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Turn on a specific VeSync device.
    """
    # Get the VeSync account
    account = await get_vesync_account_or_404(account_id, db)
    
    # Get the device from database
    device_result = await db.execute(
        select(SmartOutlet).filter(
            SmartOutlet.id == device_id,
            SmartOutlet.vesync_account_id == account_id,
            SmartOutlet.driver_type == "vesync"
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VeSync device not found"
        )
    
    # Turn on the device
    try:
        await vesync_device_service.turn_device_on(account, device.driver_device_id)
        
        # Get updated state
        state = await vesync_device_service.get_device_state(account, device.driver_device_id)
        
        # Combine database data with real-time state
        device_data = SmartOutletRead.model_validate(device).model_dump()
        device_data.update(state)
        
        return SmartOutletWithState(**device_data)
        
    except (OutletAuthenticationError, OutletConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@vesync_router.post("/{account_id}/devices/{device_id}/turn_off", response_model=SmartOutletWithState)
async def turn_off_vesync_device(
    account_id: int, 
    device_id: str, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Turn off a specific VeSync device.
    """
    # Get the VeSync account
    account = await get_vesync_account_or_404(account_id, db)
    
    # Get the device from database
    device_result = await db.execute(
        select(SmartOutlet).filter(
            SmartOutlet.id == device_id,
            SmartOutlet.vesync_account_id == account_id,
            SmartOutlet.driver_type == "vesync"
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VeSync device not found"
        )
    
    # Turn off the device
    try:
        await vesync_device_service.turn_device_off(account, device.driver_device_id)
        
        # Get updated state
        state = await vesync_device_service.get_device_state(account, device.driver_device_id)
        
        # Combine database data with real-time state
        device_data = SmartOutletRead.model_validate(device).model_dump()
        device_data.update(state)
        
        return SmartOutletWithState(**device_data)
        
    except (OutletAuthenticationError, OutletConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        ) 