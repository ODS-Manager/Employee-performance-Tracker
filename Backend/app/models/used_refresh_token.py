"""
Used Refresh Token Model
Stores refresh tokens that have already been used (one-time use enforcement).
"""
from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from app.database import Base


class UsedRefreshToken(Base):
    """Stores used refresh tokens"""
    __tablename__ = "used_refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    used_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
