from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from temp.config import settings

# HTTP Bearer token scheme
security = HTTPBearer()

async def verify_service_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verify the service token for authentication.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        str: The verified token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    if not token or token != settings.SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

# Dependency for authenticated endpoints
get_verified_token = Depends(verify_service_token) 