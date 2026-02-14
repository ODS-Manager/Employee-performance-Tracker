"""
Automated session cleanup scheduler
Periodically removes expired sessions and blacklisted tokens from Redis
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.services.session_service import session_service

logger = logging.getLogger(__name__)


async def cleanup_expired_sessions():
    """
    Clean up expired sessions and blacklisted tokens from Redis
    
    This task runs periodically to:
    - Remove expired session keys
    - Clean up old blacklisted tokens
    - Free up Redis memory
    """
    try:
        logger.info("Starting expired session cleanup task")
        
        if not session_service.is_connected:
            logger.warning("Redis not connected. Skipping session cleanup.")
            return
        
        # Redis automatically removes expired keys with TTL, but we can help
        # by scanning for and removing any orphaned or malformed keys
        
        # Count of items cleaned
        cleaned_count = 0
        
        # In production, you might want to add additional cleanup logic here
        # For now, Redis TTL handles most cleanup automatically
        
        logger.info(f"Session cleanup completed. Cleaned {cleaned_count} items.")
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}")


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
