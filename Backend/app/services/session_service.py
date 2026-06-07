"""
PostgreSQL-based Session and Token Management Service
Provides token blacklisting, active session tracking, rate limiting, and refresh token rotation
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from app.core.config import settings
from app.database import SessionLocal
from app.models.blacklisted_token import BlacklistedToken
from app.models.user_session import UserSession
from app.models.used_refresh_token import UsedRefreshToken
from app.models.rate_limit import RateLimit
from app.models.login_attempt import LoginAttempt

logger = logging.getLogger(__name__)


class SessionService:
    """PostgreSQL-based session and token management service"""
    
    # TTL constants (in seconds)
    TTL_ACCESS_TOKEN = 60 * 60  # 1 hour
    TTL_REFRESH_TOKEN = 60 * 60 * 24 * 30  # 30 days
    TTL_RATE_LIMIT = 60  # 1 minute
    TTL_LOGIN_ATTEMPTS = 60 * 15  # 15 minutes
    
    # Rate limiting settings
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_LOGIN_ATTEMPTS = 5
    
    _instance: Optional['SessionService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if session service is available (always True with PostgreSQL)"""
        return True
    
    # ============ Token Blacklist Management ============
    
    def blacklist_token(self, jti: str, ttl: Optional[int] = None) -> bool:
        """Add a token to the blacklist"""
        db = SessionLocal()
        try:
            ttl = ttl or self.TTL_ACCESS_TOKEN
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            token = BlacklistedToken(jti=jti, expires_at=expires_at)
            db.add(token)
            db.commit()
            logger.info(f"Token {jti} blacklisted successfully")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error blacklisting token {jti}: {e}")
            return False
        finally:
            db.close()
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted"""
        db = SessionLocal()
        try:
            token = db.query(BlacklistedToken).filter(
                BlacklistedToken.jti == jti,
                BlacklistedToken.expires_at > datetime.utcnow()
            ).first()
            return token is not None
        except Exception as e:
            logger.error(f"Error checking token blacklist for {jti}: {e}")
            return False
        finally:
            db.close()
    
    # ============ Active Session Management ============
    
    def create_session(
        self,
        user_id: int,
        jti: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        fingerprint: Optional[str] = None
    ) -> str:
        """Create a new active session with fingerprinting and session limits"""
        db = SessionLocal()
        try:
            # Enforce session limits before creating new session
            self._enforce_session_limits(user_id)
            
            session_id = jti
            expires_at = datetime.utcnow() + timedelta(seconds=self.TTL_ACCESS_TOKEN)
            
            session = UserSession(
                user_id=user_id,
                session_id=session_id,
                device_info=device_info or "Unknown",
                ip_address=ip_address or "Unknown",
                user_agent=user_agent or "Unknown",
                fingerprint=fingerprint,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                expires_at=expires_at
            )
            db.add(session)
            db.commit()
            logger.info(f"Session {session_id} created for user {user_id}")
            return session_id
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating session for user {user_id}: {e}")
            return jti
        finally:
            db.close()
    
    def get_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.session_id == session_id,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                return {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "jti": session.session_id,
                    "device_info": session.device_info,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "fingerprint": session.fingerprint,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                    "expires_in_seconds": max(0, int((session.expires_at - datetime.utcnow()).total_seconds()))
                }
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id} for user {user_id}: {e}")
            return None
        finally:
            db.close()
    
    def update_session_activity(self, user_id: int, session_id: str) -> bool:
        """Update session last activity timestamp and extend TTL"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.session_id == session_id,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                session.last_activity = datetime.utcnow()
                session.expires_at = datetime.utcnow() + timedelta(seconds=self.TTL_ACCESS_TOKEN)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating session activity {session_id}: {e}")
            return False
        finally:
            db.close()
    
    def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        db = SessionLocal()
        try:
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            ).order_by(UserSession.created_at.desc()).all()
            
            result = []
            for session in sessions:
                result.append({
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "jti": session.session_id,
                    "device_info": session.device_info,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "fingerprint": session.fingerprint,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                    "expires_in_seconds": max(0, int((session.expires_at - datetime.utcnow()).total_seconds()))
                })
            return result
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []
        finally:
            db.close()
    
    def revoke_session(self, user_id: int, session_id: str) -> bool:
        """Revoke a specific session (logout from specific device)"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.session_id == session_id
            ).first()
            
            if session:
                jti = session.session_id
                self.blacklist_token(jti)
                db.delete(session)
                db.commit()
                logger.info(f"Session {session_id} revoked for user {user_id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error revoking session {session_id} for user {user_id}: {e}")
            return False
        finally:
            db.close()
    
    def revoke_all_user_sessions(self, user_id: int) -> int:
        """Revoke all sessions for a user (logout from all devices)"""
        db = SessionLocal()
        try:
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            ).all()
            
            count = 0
            for session in sessions:
                self.blacklist_token(session.session_id)
                db.delete(session)
                count += 1
            
            db.commit()
            logger.info(f"All {count} sessions revoked for user {user_id}")
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"Error revoking all sessions for user {user_id}: {e}")
            return 0
        finally:
            db.close()
    
    def _enforce_session_limits(self, user_id: int) -> None:
        """Enforce maximum concurrent sessions per user"""
        db = SessionLocal()
        try:
            max_sessions = getattr(settings, 'MAX_CONCURRENT_SESSIONS_PER_USER', 5)
            
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            ).order_by(UserSession.created_at.asc()).all()
            
            if len(sessions) >= max_sessions:
                num_to_remove = len(sessions) - max_sessions + 1
                for i in range(num_to_remove):
                    session_to_remove = sessions[i]
                    self.revoke_session(user_id, session_to_remove.session_id)
                    logger.info(f"Session {session_to_remove.session_id} removed due to session limit for user {user_id}")
        except Exception as e:
            logger.error(f"Error enforcing session limits for user {user_id}: {e}")
        finally:
            db.close()
    
    def validate_session_fingerprint(self, user_id: int, session_id: str, current_fingerprint: str) -> bool:
        """Validate session fingerprint to detect potential hijacking"""
        try:
            session = self.get_session(user_id, session_id)
            if not session:
                return False
            
            stored_fingerprint = session.get("fingerprint")
            if not stored_fingerprint:
                return True
            
            if stored_fingerprint != current_fingerprint:
                logger.warning(f"Fingerprint mismatch for session {session_id}, user {user_id}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating fingerprint for session {session_id}: {e}")
            return True
    
    def get_session_by_jti(self, user_id: int, jti: str) -> Optional[Dict[str, Any]]:
        """Get session by JTI"""
        return self.get_session(user_id, jti)
    
    # ============ Refresh Token Rotation ============
    
    def mark_refresh_token_used(self, jti: str) -> bool:
        """Mark a refresh token as used (for one-time use enforcement)"""
        db = SessionLocal()
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=self.TTL_REFRESH_TOKEN)
            token = UsedRefreshToken(jti=jti, expires_at=expires_at)
            db.add(token)
            db.commit()
            logger.info(f"Refresh token {jti} marked as used")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking refresh token {jti} as used: {e}")
            return False
        finally:
            db.close()
    
    def is_refresh_token_used(self, jti: str) -> bool:
        """Check if a refresh token has already been used"""
        db = SessionLocal()
        try:
            token = db.query(UsedRefreshToken).filter(
                UsedRefreshToken.jti == jti,
                UsedRefreshToken.expires_at > datetime.utcnow()
            ).first()
            return token is not None
        except Exception as e:
            logger.error(f"Error checking refresh token usage {jti}: {e}")
            return False
        finally:
            db.close()
    
    # ============ Rate Limiting ============
    
    def check_rate_limit(self, identifier: str, max_requests: Optional[int] = None, window: Optional[int] = None) -> bool:
        """Check if rate limit is exceeded"""
        db = SessionLocal()
        try:
            max_requests = max_requests or self.MAX_REQUESTS_PER_MINUTE
            window = window or self.TTL_RATE_LIMIT
            now = datetime.utcnow()
            
            # Clean old expired rate limits for this identifier
            db.query(RateLimit).filter(
                RateLimit.identifier == identifier,
                RateLimit.window_end < now
            ).delete(synchronize_session=False)
            
            rate_limit = db.query(RateLimit).filter(
                RateLimit.identifier == identifier,
                RateLimit.window_end > now
            ).first()
            
            if rate_limit is None:
                rate_limit = RateLimit(
                    identifier=identifier,
                    request_count=1,
                    window_start=now,
                    window_end=now + timedelta(seconds=window)
                )
                db.add(rate_limit)
                db.commit()
                return True
            
            if rate_limit.request_count >= max_requests:
                logger.warning(f"Rate limit exceeded for {identifier}")
                return False
            
            rate_limit.request_count += 1
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error checking rate limit for {identifier}: {e}")
            return True
        finally:
            db.close()
    
    def increment_rate_limit(self, identifier: str, window: Optional[int] = None) -> int:
        """Increment rate limit counter"""
        db = SessionLocal()
        try:
            window = window or self.TTL_RATE_LIMIT
            now = datetime.utcnow()
            
            db.query(RateLimit).filter(
                RateLimit.identifier == identifier,
                RateLimit.window_end < now
            ).delete(synchronize_session=False)
            
            rate_limit = db.query(RateLimit).filter(
                RateLimit.identifier == identifier,
                RateLimit.window_end > now
            ).first()
            
            if rate_limit is None:
                rate_limit = RateLimit(
                    identifier=identifier,
                    request_count=1,
                    window_start=now,
                    window_end=now + timedelta(seconds=window)
                )
                db.add(rate_limit)
                db.commit()
                return 1
            
            rate_limit.request_count += 1
            db.commit()
            return rate_limit.request_count
        except Exception as e:
            db.rollback()
            logger.error(f"Error incrementing rate limit for {identifier}: {e}")
            return 0
        finally:
            db.close()
    
    # ============ Login Attempt Tracking ============
    
    def record_login_attempt(self, identifier: str, success: bool) -> int:
        """Record a login attempt"""
        db = SessionLocal()
        try:
            attempt = db.query(LoginAttempt).filter(
                LoginAttempt.identifier == identifier
            ).first()
            
            if success:
                if attempt:
                    db.delete(attempt)
                    db.commit()
                return 0
            
            now = datetime.utcnow()
            if attempt is None:
                attempt = LoginAttempt(
                    identifier=identifier,
                    failed_count=1,
                    last_attempt_at=now
                )
                db.add(attempt)
            else:
                attempt.failed_count += 1
                attempt.last_attempt_at = now
                if attempt.failed_count >= self.MAX_LOGIN_ATTEMPTS:
                    attempt.block_until = now + timedelta(minutes=settings.LOGIN_BLOCK_DURATION_MINUTES)
            
            db.commit()
            return attempt.failed_count
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording login attempt for {identifier}: {e}")
            return 0
        finally:
            db.close()
    
    def get_login_attempts(self, identifier: str) -> int:
        """Get number of failed login attempts"""
        db = SessionLocal()
        try:
            attempt = db.query(LoginAttempt).filter(
                LoginAttempt.identifier == identifier
            ).first()
            return attempt.failed_count if attempt else 0
        except Exception as e:
            logger.error(f"Error getting login attempts for {identifier}: {e}")
            return 0
        finally:
            db.close()
    
    def is_login_blocked(self, identifier: str) -> bool:
        """Check if login is blocked due to too many failed attempts"""
        db = SessionLocal()
        try:
            attempt = db.query(LoginAttempt).filter(
                LoginAttempt.identifier == identifier
            ).first()
            
            if not attempt:
                return False
            
            now = datetime.utcnow()
            if attempt.block_until and attempt.block_until > now:
                return True
            
            # If no explicit block but count exceeds max, check if within window
            if attempt.failed_count >= self.MAX_LOGIN_ATTEMPTS:
                # Block if last attempt was within the tracking window
                if attempt.last_attempt_at and attempt.last_attempt_at > now - timedelta(seconds=self.TTL_LOGIN_ATTEMPTS):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking login block for {identifier}: {e}")
            return False
        finally:
            db.close()
    
    def get_login_block_ttl(self, identifier: str) -> int:
        """Get remaining seconds until login block expires"""
        db = SessionLocal()
        try:
            attempt = db.query(LoginAttempt).filter(
                LoginAttempt.identifier == identifier
            ).first()
            
            if not attempt:
                return 0
            
            now = datetime.utcnow()
            if attempt.block_until and attempt.block_until > now:
                return max(0, int((attempt.block_until - now).total_seconds()))
            
            # If blocked by count but no explicit block_until, return time until attempt window expires
            if attempt.failed_count >= self.MAX_LOGIN_ATTEMPTS and attempt.last_attempt_at:
                window_end = attempt.last_attempt_at + timedelta(seconds=self.TTL_LOGIN_ATTEMPTS)
                if window_end > now:
                    return max(0, int((window_end - now).total_seconds()))
            
            return 0
        except Exception as e:
            logger.error(f"Error getting login block TTL for {identifier}: {e}")
            return 0
        finally:
            db.close()


# Global session service instance
session_service = SessionService()
