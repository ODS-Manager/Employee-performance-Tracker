"""
Login Attempt Model
Tracks failed login attempts per identifier for brute-force protection.
"""
from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from app.database import Base


class LoginAttempt(Base):
    """Stores login attempt tracking"""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(255), unique=True, nullable=False, index=True)
    failed_count = Column(Integer, default=1, nullable=False)
    last_attempt_at = Column(DateTime, default=datetime.utcnow)
    block_until = Column(DateTime, nullable=True)
