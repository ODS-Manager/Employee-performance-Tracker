"""
Automated session cleanup scheduler
Periodically removes expired sessions and blacklisted tokens from PostgreSQL
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models.blacklisted_token import BlacklistedToken
from app.models.user_session import UserSession
from app.models.used_refresh_token import UsedRefreshToken
from app.models.rate_limit import RateLimit
from app.models.login_attempt import LoginAttempt

logger = logging.getLogger(__name__)


async def cleanup_expired_sessions():
    """
    Clean up expired sessions and security data from PostgreSQL.
    
    This task runs periodically to:
    - Remove expired blacklisted tokens
    - Remove expired user sessions
    - Remove expired used refresh tokens
    - Remove expired rate limit records
    - Remove stale login attempt records
    """
    db = SessionLocal()
    try:
        logger.info("Starting expired session cleanup task")
        now = datetime.utcnow()
        total_cleaned = 0
        
        # Clean expired blacklisted tokens
        result = db.query(BlacklistedToken).filter(BlacklistedToken.expires_at < now).delete(synchronize_session=False)
        total_cleaned += result
        logger.info(f"Cleaned {result} expired blacklisted tokens")
        
        # Clean expired user sessions
        result = db.query(UserSession).filter(UserSession.expires_at < now).delete(synchronize_session=False)
        total_cleaned += result
        logger.info(f"Cleaned {result} expired user sessions")
        
        # Clean expired used refresh tokens
        result = db.query(UsedRefreshToken).filter(UsedRefreshToken.expires_at < now).delete(synchronize_session=False)
        total_cleaned += result
        logger.info(f"Cleaned {result} expired used refresh tokens")
        
        # Clean expired rate limits
        result = db.query(RateLimit).filter(RateLimit.window_end < now).delete(synchronize_session=False)
        total_cleaned += result
        logger.info(f"Cleaned {result} expired rate limits")
        
        # Clean stale login attempts (blocked attempts where block has expired, or non-blocked older than 15 min)
        stale_cutoff = now - timedelta(minutes=15)
        result = db.query(LoginAttempt).filter(
            (LoginAttempt.block_until.isnot(None) & (LoginAttempt.block_until < now)) |
            (LoginAttempt.block_until.is_(None) & (LoginAttempt.last_attempt_at < stale_cutoff))
        ).delete(synchronize_session=False)
        total_cleaned += result
        logger.info(f"Cleaned {result} stale login attempts")
        
        db.commit()
        logger.info(f"Session cleanup completed. Total cleaned: {total_cleaned} items.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during session cleanup: {e}")
    finally:
        db.close()


def start_session_cleanup_scheduler() -> AsyncIOScheduler:
    """
    Start the session cleanup scheduler
    
    Runs cleanup task every 1 hour
    
    Returns:
        AsyncIOScheduler instance
    """
    scheduler = AsyncIOScheduler()
    
    # Schedule cleanup every hour
    scheduler.add_job(
        cleanup_expired_sessions,
        trigger=IntervalTrigger(hours=1),
        id='session_cleanup',
        name='Clean up expired sessions',
        replace_existing=True,
        misfire_grace_time=300  # 5 minutes grace time if missed
    )
    
    logger.info("Session cleanup scheduler initialized")
    return scheduler


async def run_cleanup_now():
    """
    Run cleanup task immediately (for testing or manual execution)
    """
    await cleanup_expired_sessions()
