"""
Rate Limit Model
Stores per-identifier request counts within a time window.
"""
from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from app.database import Base


class RateLimit(Base):
    """Stores rate limit counters"""
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(255), nullable=False, index=True)
    request_count = Column(Integer, default=1, nullable=False)
    window_start = Column(DateTime, default=datetime.utcnow)
    window_end = Column(DateTime, nullable=False)
