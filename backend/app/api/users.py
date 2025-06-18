from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_current_active_admin
from app.crud.user import get_user_by_username
from app.db.base import get_db
from app.schemas.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user = Depends(get_current_user)
) -> User:
    """
    Get current user information.
    """
    return current_user

@router.get("/", response_model=list[User])
async def get_users(
    current_user = Depends(get_current_active_admin)
) -> list[User]:
    """
    Get all users (admin only).
    """
    # TODO: Implement get all users logic
    # For now, return empty list
    return [] 