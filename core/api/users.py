from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.api.deps import get_current_user, get_current_active_admin
from shared.crud.user import get_user_by_username, get_users, get_user, update_user, delete_user
from shared.db.database import get_db
from shared.schemas.user import User, UserUpdate

router = APIRouter(tags=["users"])

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user = Depends(get_current_user)
) -> User:
    """
    Get current user information.
    """
    return current_user

@router.get("/", response_model=list[User])
async def get_users_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_admin)
) -> list[User]:
    """
    Get all users (admin only).
    """
    users = await get_users(db)
    return users

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_admin)
) -> User:
    """
    Get a specific user by ID (admin only).
    """
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.patch("/{user_id}", response_model=User)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_admin)
) -> User:
    """
    Update a user (admin only).
    """
    updated_user = await update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

@router.patch("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> User:
    """
    Update current user's own information.
    """
    updated_user = await update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

@router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_admin)
):
    """
    Delete a user (admin only).
    """
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"} 