from sqlalchemy import Boolean, Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # No explicit indexes needed - unique=True already creates indexes
    # __table_args__ = (
    #     Index('ix_users_email', 'email', unique=True),
    #     Index('ix_users_username', 'username', unique=True),
    # ) 