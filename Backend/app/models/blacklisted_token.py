"""
Blacklisted Token Model
Stores revoked JWT tokens for logout / password-change invalidation.
"""
from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from app.database import Base


class BlacklistedToken(Base):
    """Stores blacklisted JWT tokens"""
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
