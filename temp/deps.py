from fastapi import Header, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from shared.db.database import SessionLocal
from .config import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="Authorization header is missing")
    
    token_type, _, token = api_key.partition(' ')
    if token_type.lower() != 'bearer' or not token:
        raise HTTPException(status_code=403, detail="Invalid token type. Use Bearer token.")

    if token == settings.SERVICE_TOKEN:
        return token
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")