"""
Security Middleware
CSRF protection and security headers middleware
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security_utils import CSRFProtection, SecurityAuditLogger, get_client_ip


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware
    Validates CSRF tokens for state-changing requests
    """
    
    # Paths that don't require CSRF protection
    EXEMPT_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/auth/login",  # Login creates CSRF token
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)
        
        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Validate CSRF token
        if not CSRFProtection.validate_csrf_token(request):
            # Log security event
            await SecurityAuditLogger.log_security_event(
                event_type=SecurityAuditLogger.EVENT_CSRF_VALIDATION_FAILED,
                user_id=None,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                additional_data={"path": request.url.path, "method": request.method}
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed"
            )
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security Headers Middleware
    Adds security-related HTTP headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict Transport Security (HTTPS only)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )
        
        return response
