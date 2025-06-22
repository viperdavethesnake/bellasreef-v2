from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import async_session
from shared.core.config import settings
from core.api.deps import get_current_user # We still need this for user auth
from shared.schemas.user import User

# This header is for the static SERVICE_TOKEN
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def verify_service_token(api_key: str = Security(api_key_header)):
    """A dependency to verify the static service token."""
    if not api_key:
        return None # Allow JWT check to proceed

    token_type, _, token = api_key.partition(' ')
    if token_type.lower() != 'bearer' or not token:
        return None # Not a valid bearer token, allow JWT check

    if token == settings.SERVICE_TOKEN:
        return token # Success! It's the service token.

    return None # Not the service token, allow JWT check

async def require_auth(
    user: User = Depends(get_current_user),
    service_token: str = Depends(verify_service_token)
):
    """
    A dependency that requires EITHER a valid JWT token OR the static service token.
    This allows both users and internal services to access an endpoint.
    """
    if user is None and service_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user or service_token