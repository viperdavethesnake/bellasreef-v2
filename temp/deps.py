from sqlalchemy.orm import Session
from shared.db.database import async_session

async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise