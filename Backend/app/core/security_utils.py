"""
Security Utilities
CSRF protection, session fingerprinting, and security audit logging
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, Response
from app.core.config import settings


class CSRFProtection:
    """CSRF token generation and validation using double-submit cookie pattern"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a random CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def set_csrf_cookie(response: Response, token: str) -> None:
        """
        Set CSRF token as a cookie
        Note: httpOnly is False so JavaScript can read it for headers
        """
        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=token,
            max_age=settings.CSRF_TOKEN_EXPIRE_MINUTES * 60,
            httponly=False,  # Must be readable by JavaScript
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            domain=settings.COOKIE_DOMAIN,
            path="/"
        )
    
    @staticmethod
    def validate_csrf_token(request: Request) -> bool:
        """
        Validate CSRF token using double-submit pattern
        Returns True if valid, False otherwise
        """
        # Skip validation for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        
        # Get CSRF token from header
        csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)
        
        # Get CSRF token from cookie
        csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
        
        # Both must exist and match
        if not csrf_header or not csrf_cookie:
            return False
        
        return secrets.compare_digest(csrf_header, csrf_cookie)


class SessionSecurity:
    """Session fingerprinting and security features"""
    
    @staticmethod
    def generate_fingerprint(request: Request) -> str:
        """
        Generate session fingerprint for anomaly detection
        Based on User-Agent, Accept-Language, and Accept-Encoding
        """
        user_agent = request.headers.get("user-agent", "")
        accept_language = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")
        
        fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    @staticmethod
    def validate_session_fingerprint(stored_fingerprint: str, current_fingerprint: str) -> bool:
        """
        Validate session fingerprint hasn't changed
        Returns True if valid, False if potential hijacking detected
        """
        return secrets.compare_digest(stored_fingerprint, current_fingerprint)
    
    @staticmethod
    def extract_device_info(user_agent: str) -> str:
        """Extract simplified device info from user agent"""
        if not user_agent or user_agent == "Unknown":
            return "Unknown"
        
        # Simple extraction - get first part
        parts = user_agent.split()
        return parts[0] if parts else "Unknown"


class SecurityAuditLogger:
    """Security event logging for monitoring and analysis"""
    
    # Security event types
    EVENT_SUCCESSFUL_LOGIN = "SUCCESSFUL_LOGIN"
    EVENT_FAILED_LOGIN = "FAILED_LOGIN_ATTEMPT"
    EVENT_LOGOUT = "LOGOUT"
    EVENT_PASSWORD_CHANGE = "PASSWORD_CHANGE"
    EVENT_TOKEN_REFRESH = "TOKEN_REFRESH"
    EVENT_INVALID_TOKEN = "INVALID_TOKEN"
    EVENT_BLACKLISTED_TOKEN = "BLACKLISTED_TOKEN_ATTEMPT"
    EVENT_CSRF_VALIDATION_FAILED = "CSRF_VALIDATION_FAILED"
    EVENT_SESSION_HIJACKING = "POTENTIAL_SESSION_HIJACKING"
    EVENT_TOKEN_REUSE = "TOKEN_REUSE_DETECTED"
    EVENT_MULTIPLE_FAILED_LOGINS = "MULTIPLE_FAILED_LOGINS"
    EVENT_SESSION_LIMIT_ENFORCED = "SESSION_LIMIT_ENFORCED"
    EVENT_ALL_SESSIONS_REVOKED = "ALL_SESSIONS_REVOKED"
    
    @staticmethod
    async def log_security_event(
        event_type: str,
        user_id: Optional[int],
        ip_address: str,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security events for monitoring and analysis
        
        Args:
            event_type: Type of security event
            user_id: User ID involved (None if not authenticated)
            ip_address: Client IP address
            user_agent: Client user agent string
            session_id: Session ID if applicable
            additional_data: Any additional context data
        """
        import logging
        logger = logging.getLogger(__name__)
        
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": session_id,
            "additional_data": additional_data or {}
        }
        
        # Log at appropriate level based on severity
        if event_type in [
            SecurityAuditLogger.EVENT_SESSION_HIJACKING,
            SecurityAuditLogger.EVENT_TOKEN_REUSE,
            SecurityAuditLogger.EVENT_MULTIPLE_FAILED_LOGINS,
            SecurityAuditLogger.EVENT_CSRF_VALIDATION_FAILED
        ]:
            logger.warning(f"Security Event: {event_type}", extra=audit_data)
        else:
            logger.info(f"Security Event: {event_type}", extra=audit_data)
        
        # TODO: In production, also send critical events to monitoring system
        # e.g., Sentry, CloudWatch, etc.
    
    @staticmethod
    async def trigger_security_alert(audit_data: Dict[str, Any]) -> None:
        """
        Trigger immediate alert for critical security events
        
        Args:
            audit_data: Security event data
        """
        # TODO: Implement alert system
        # This could send emails, Slack notifications, or trigger monitoring alerts
        pass


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request
    Handles X-Forwarded-For for proxy/load balancer scenarios
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get first IP in chain (client IP)
        return forwarded_for.split(",")[0].strip()
    
    return request.client.host if request.client else "Unknown"


def set_token_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_token_max_age: int,
    refresh_token_max_age: int
) -> None:
    """
    Set access and refresh tokens as httpOnly cookies
    
    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
        access_token_max_age: Max age in seconds for access token
        refresh_token_max_age: Max age in seconds for refresh token
    """
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_token_max_age,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/api"
    )
    
    # Set refresh token cookie
    # Use more restrictive path for refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_token_max_age,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth/refresh"
    )


def clear_token_cookies(response: Response) -> None:
    """Clear authentication cookies on logout"""
    response.delete_cookie(key="access_token", path="/api")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
    response.delete_cookie(key=settings.CSRF_COOKIE_NAME, path="/")
