"""
SmartOutlet API Routes

This module defines FastAPI routes for smart outlet operations, including
creation, update, control, and discovery of smart outlets. All endpoints
are documented for OpenAPI/Swagger UI.
"""

from uuid import uuid4
from typing import List
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
from .models import SmartOutlet, VeSyncAccount
from .schemas import (
    SmartOutletCreate, SmartOutletRead, SmartOutletState, SmartOutletUpdate,
    VeSyncDiscoveryRequest, DiscoveredDevice, DiscoveryTaskResponse, DiscoveryResults,
    VeSyncAccountCreate, VeSyncAccountRead
)
from .exceptions import OutletNotFoundError, OutletConnectionError, OutletAuthenticationError
from .handlers import register_exception_handlers
from .discovery_service import DiscoveryService
from .config import settings
from .crypto_utils import encrypt_vesync_password, decrypt_vesync_password

router = APIRouter()

# Global discovery service instance
discovery_service = DiscoveryService()


def require_api_key(api_key: str = Header(..., description="API key for authentication")):
    """
    Demo authentication dependency for API routes.

    This is a placeholder implementation showing how API authentication
    will integrate with the project-wide security system in the future.

    Args:
        api_key: API key from request header

    Raises:
        HTTPException: 403 if API key is invalid
    """
    if api_key != settings.SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )


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
    dependencies=[Depends(require_api_key)],
    summary="Create a new smart outlet",
    description="Creates a new smart outlet record in the database and registers it with the manager.",
    tags=["Smart Outlets"]
)
async def create_outlet(
    outlet_data: SmartOutletCreate,
    manager: SmartOutletManager = Depends(get_smart_outlet_manager),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new smart outlet.

    Args:
        outlet_data: Smart outlet creation data
        manager: SmartOutletManager instance
        session: Database session

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
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    List all smart outlets.

    Args:
        include_disabled: Whether to include disabled outlets
        manager: SmartOutletManager instance

    Returns:
        List[SmartOutletRead]: List of outlet data
    """
    outlets = await manager.get_all_outlets(include_disabled=include_disabled)
    return [SmartOutletRead.model_validate(outlet) for outlet in outlets]


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
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Update an existing smart outlet configuration.

    Args:
        outlet_id: The ID of the outlet to update
        update_data: Update data containing allowed fields
        manager: SmartOutletManager instance

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
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Get the current state of a smart outlet.

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance

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
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Turn on a smart outlet.

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance

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
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Turn off a smart outlet.

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance

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
    manager: SmartOutletManager = Depends(get_smart_outlet_manager)
):
    """
    Toggle a smart outlet (turn off if on, turn on if off).

    Args:
        outlet_id: The ID of the outlet
        manager: SmartOutletManager instance

    Returns:
        SmartOutletState: Current outlet state after toggle
    """
    success = await manager.toggle_outlet(outlet_id)
    if success:
        # Return the current state after toggle
        return await manager.get_outlet_status(outlet_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle outlet {outlet_id}"
        )


# Discovery Endpoints

@router.post(
    "/outlets/discover/local",
    response_model=DiscoveryTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start local device discovery",
    description="Initiates asynchronous discovery of Shelly and Kasa devices on the local network.",
    tags=["Discovery"]
)
async def start_local_discovery():
    """
    Start local device discovery for Shelly and Kasa devices.

    Returns:
        DiscoveryTaskResponse: Task ID for tracking the discovery process
    """
    task_id = await discovery_service.run_local_discovery()
    return DiscoveryTaskResponse(task_id=task_id)


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

    Args:
        task_id: The task ID to retrieve results for

    Returns:
        DiscoveryResults: Discovery results and status

    Raises:
        HTTPException: 404 if task not found
    """
    results = await discovery_service.get_discovery_results(task_id)
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery task {task_id} not found"
        )
    
    # Convert results to Pydantic models
    discovered_devices = []
    for device_data in results.get('results', []):
        discovered_devices.append(DiscoveredDevice(**device_data))
    
    return DiscoveryResults(
        task_id=task_id,
        status=results['status'],
        created_at=results['created_at'],
        completed_at=results.get('completed_at'),
        results=discovered_devices,
        error=results.get('error')
    )


@router.post(
    "/outlets/discover/cloud/vesync",
    response_model=List[DiscoveredDevice],
    summary="Discover VeSync cloud devices",
    description="Discovers VeSync smart outlets using provided cloud credentials.",
    tags=["Discovery"]
)
async def discover_vesync_devices(request: VeSyncDiscoveryRequest):
    """
    Discover VeSync devices using cloud credentials.

    Args:
        request: VeSync discovery request with credentials

    Returns:
        List[DiscoveredDevice]: List of discovered VeSync devices

    Raises:
        HTTPException: If discovery fails or credentials are invalid
    """
    try:
        from .drivers.vesync import VeSyncDriver
        devices = await VeSyncDriver.discover_devices(request.email, request.password.get_secret_value())
        return devices
    except OutletAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"VeSync authentication failed for {request.email}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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
    prefix="/vesync/accounts",
    tags=["VeSync Accounts"],
    responses={404: {"description": "Not found"}},
)


@vesync_router.post("/", response_model=VeSyncAccountRead, status_code=status.HTTP_201_CREATED)
async def create_vesync_account(account: VeSyncAccountCreate, db: AsyncSession = Depends(get_db_session)):
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
        is_active=account.is_active
    )

    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account


@vesync_router.get("/", response_model=List[VeSyncAccountRead])
async def read_vesync_accounts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    """
    Retrieve all VeSync accounts.
    """
    result = await db.execute(select(VeSyncAccount).offset(skip).limit(limit))
    accounts = result.scalars().all()
    return accounts


@vesync_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vesync_account(account_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Delete a VeSync account.
    """
    db_account = await get_vesync_account_or_404(account_id, db)
    await db.delete(db_account)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@vesync_router.post("/{account_id}/verify", response_model=VeSyncAccountRead)
async def verify_vesync_account(account_id: int, db: AsyncSession = Depends(get_db_session)):
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

    manager = VeSync(db_account.email, password)
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