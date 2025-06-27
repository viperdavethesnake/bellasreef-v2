from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import async_session
from shared.core.config import settings
from shared.core.security import verify_token
from shared.crud.user import get_user_by_username
from shared.schemas.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def get_current_user_or_service(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    A dependency that authenticates EITHER a user via JWT OR a service
    via the static SERVICE_TOKEN. This is the single auth dependency to use.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # First, check if it's the static service token
    if token == settings.SERVICE_TOKEN:
        return "service" # Authentication successful for a service

    # If not, try to decode it as a user JWT
    token_data = verify_token(token)
    if token_data and token_data.username:
        user = await get_user_by_username(db, username=token_data.username)
        if user and user.is_active:
            return user # Authentication successful for a user

    # If neither works, fail
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    ) 