from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_token
from app.crud.user import get_user_by_username
from app.db.base import get_db
from app.schemas.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def get_current_user(
    current_user: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user information.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = await get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.get("/", response_model=list[User])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(verify_token)
) -> list[User]:
    """
    Get all users (admin only).
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # TODO: Add admin check
    # For now, return empty list
    return [] 