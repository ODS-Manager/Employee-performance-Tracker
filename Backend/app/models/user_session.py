"""
User Session Model
Stores active user sessions with device and fingerprint info.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from datetime import datetime
from app.database import Base


class UserSession(Base):
    """Stores active user sessions"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    device_info = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    fingerprint = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_user_sessions_user_session', 'user_id', 'session_id'),
    )
