"""
Authentication API Routes
Login, logout, token refresh, password management with session management
SECURE: Uses httpOnly cookies and CSRF protection
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiry
)
from app.core.dependencies import get_current_active_user
from app.core.security_utils import (
    CSRFProtection,
    SessionSecurity,
    SecurityAuditLogger,
    get_client_ip,
    set_token_cookies,
    clear_token_cookies
)
from app.services.session_service import session_service
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse,
    SessionResponse,
    SessionListResponse,
    RevokeSessionRequest,
    RevokeAllSessionsResponse
)

router = APIRouter()


@router.get("/debug")
async def debug_login():
    """Debug endpoint to check database content"""
    import os
    from app.core.config import settings
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        
        # Test basic connection
        result = db.execute(text("SELECT COUNT(*) as total FROM users"))
        user_count = result.fetchone()[0]
        
        # Get sample users
        result = db.execute(text("SELECT user_name, password_hash FROM users LIMIT 5"))
        users = result.fetchall()
        
        # Check for organizations table
        try:
            org_result = db.execute(text("SELECT COUNT(*) as total FROM organizations"))
            org_count = org_result.fetchone()[0]
            
            org_list_result = db.execute(text("SELECT name, code FROM organizations LIMIT 5"))
            organizations = org_list_result.fetchall()
            org_data = [{"name": row[0], "code": row[1]} for row in organizations]
        except Exception as org_error:
            org_count = 0
            org_data = []
            print(f"Organizations table error: {org_error}")
        
        # Check for teams table
        try:
            team_result = db.execute(text("SELECT COUNT(*) as total FROM teams"))
            team_count = team_result.fetchone()[0]
        except Exception as team_error:
            team_count = 0
            print(f"Teams table error: {team_error}")
        
        db.close()
        
        return {
            "status": "success",
            "database_url_type": "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite",
            "database_url_preview": settings.DATABASE_URL[:80] + "..." if len(settings.DATABASE_URL) > 80 else settings.DATABASE_URL,
            "socket_path": "/cloudsql/project-0990a5d7-310c-4a56-837:asia-south1:ods-database/.s.PGSQL.5432" if "cloudsql" in settings.DATABASE_URL else "N/A",
            "connection_test": "successful",
            "total_users": user_count,
            "total_organizations": org_count,
            "total_teams": team_count,
            "sample_users": [{"user_name": row[0], "hash_preview": row[1][:20] + "..."} for row in users],
            "sample_organizations": org_data
        }
    except Exception as e:
        from app.core.config import settings
        return {
            "status": "error",
            "error": str(e),
            "database_url_type": "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite",
            "database_url_preview": settings.DATABASE_URL[:80] + "..." if len(settings.DATABASE_URL) > 80 else settings.DATABASE_URL,
            "socket_path": "/cloudsql/project-0990a5d7-310c-4a56-837:asia-south1:ods-database/.s.PGSQL.5432" if "cloudsql" in settings.DATABASE_URL else "N/A",
            "connection_test": "failed"
        }


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate user and return tokens with session management
    
    Features:
    - Rate limiting (5 attempts per 15 minutes)
    - Login attempt tracking
    - Active session creation with fingerprinting
    - Device and IP tracking
    - httpOnly cookie-based authentication
    - CSRF protection
    """
    # Get client information
    client_ip = get_client_ip(req)
    user_agent = req.headers.get("user-agent", "Unknown")
    
    # Create identifier for rate limiting (username + IP)
    rate_limit_identifier = f"{request.user_name}:{client_ip}"
    
    # Check if login is blocked due to too many failed attempts
    try:
        if session_service.is_login_blocked(rate_limit_identifier):
            remaining_time = session_service.get_login_block_ttl(rate_limit_identifier)
            
            # Log failed login attempt
            await SecurityAuditLogger.log_security_event(
                SecurityAuditLogger.EVENT_FAILED_LOGIN,
                None,
                client_ip,
                user_agent,
                None,
                {"reason": "rate_limited", "username": request.user_name}
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again in {remaining_time} seconds."
            )
    except HTTPException:
        raise
    except Exception as e:
        # Continue with rate limiting disabled if session service fails
        pass
    
    # Find user by username
    user = db.query(User).filter(User.user_name == request.user_name).first()
    
    if not user:
        # Record failed attempt
        try:
            session_service.record_login_attempt(rate_limit_identifier, success=False)
        except:
            pass
        
        # Log failed login attempt
        await SecurityAuditLogger.log_security_event(
            SecurityAuditLogger.EVENT_FAILED_LOGIN,
            None,
            client_ip,
            user_agent,
            None,
            {"reason": "invalid_username", "username": request.user_name}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not verify_password(request.password, user.password_hash):
        # Record failed attempt
        try:
            session_service.record_login_attempt(rate_limit_identifier, success=False)
        except:
            pass
        
        # Log failed login attempt
        await SecurityAuditLogger.log_security_event(
            SecurityAuditLogger.EVENT_FAILED_LOGIN,
            user.id,
            client_ip,
            user_agent,
            None,
            {"reason": "invalid_password"}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        # Log failed login attempt
        await SecurityAuditLogger.log_security_event(
            SecurityAuditLogger.EVENT_FAILED_LOGIN,
            user.id,
            client_ip,
            user_agent,
            None,
            {"reason": "account_inactive"}
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Successful login - clear failed attempts
    try:
        session_service.record_login_attempt(rate_limit_identifier, success=True)
    except:
        pass
    
    # Update last login
    try:
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
    except Exception as e:
        # Continue without updating last login
        pass
    
    # Generate unique JTIs for access and refresh tokens
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())
    
    # Generate CSRF token
    csrf_token = CSRFProtection.generate_csrf_token()
    
    # Generate session fingerprint
    fingerprint = SessionSecurity.generate_fingerprint(req)
    
    # Create tokens with version
    token_data = {
        "sub": str(user.id),
        "role": user.user_role,
        "userName": user.user_name,
        "orgId": user.org_id,
        "version": user.token_version
    }
    
    access_token = create_access_token(token_data, jti=access_jti)
    refresh_token = create_refresh_token(token_data, jti=refresh_jti)
    
    # Set tokens as httpOnly cookies
    set_token_cookies(
        response,
        access_token,
        refresh_token,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    # Set CSRF cookie
    CSRFProtection.set_csrf_cookie(response, csrf_token)
    
    # Create session in Redis with fingerprint
    device_info = user_agent.split()[0] if user_agent != "Unknown" else "Unknown"
    try:
        session_service.create_session(
            user_id=user.id,
            jti=access_jti,
            device_info=device_info,
            ip_address=client_ip,
            user_agent=user_agent,
            fingerprint=fingerprint
        )
    except Exception as e:
        # If session creation fails, log but continue
        print(f"Session creation error: {e}")
    
    # Log successful login
    await SecurityAuditLogger.log_security_event(
        SecurityAuditLogger.EVENT_SUCCESSFUL_LOGIN,
        user.id,
        client_ip,
        user_agent
    )
    
    # Return user data only (no tokens) - Pydantic will handle serialization
    user_response = UserResponse.model_validate(user)
    
    return LoginResponse(
        success=True,
        message="Login successful",
        user=user_response
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(req: Request, response: Response, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token with rotation
    
    Features:
    - One-time use refresh tokens
    - Automatic refresh token rotation
    - Detects token reuse (potential security breach)
    - httpOnly cookie-based authentication
    """
    # Extract refresh token from cookie
    refresh_token_value = req.cookies.get("refresh_token")
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )
    
    payload = decode_token(refresh_token_value)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Extract JTI and check if already used (one-time use)
    jti = payload.get("jti")
    if jti and session_service.is_refresh_token_used(jti):
        # Token reuse detected - possible security breach
        user_id = payload.get("sub")
        if user_id:
            session_service.revoke_all_user_sessions(int(user_id))
            
            # Log security alert
            await SecurityAuditLogger.log_security_event(
                SecurityAuditLogger.EVENT_TOKEN_REUSE,
                int(user_id),
                get_client_ip(req),
                req.headers.get("user-agent"),
                {"jti": jti}
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has already been used. All sessions have been terminated for security."
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Check token version
    token_version = payload.get("version", 0)
    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated. Please login again."
        )
    
    # Mark old refresh token as used
    if jti:
        session_service.mark_refresh_token_used(jti)
    
    # Generate new JTIs
    new_access_jti = str(uuid.uuid4())
    new_refresh_jti = str(uuid.uuid4())
    
    # Get client information for session
    client_ip = get_client_ip(req)
    user_agent = req.headers.get("user-agent", "Unknown")
    device_info = user_agent.split()[0] if user_agent != "Unknown" else "Unknown"
    
    # Generate session fingerprint
    fingerprint = SessionSecurity.generate_fingerprint(req)
    
    # Create new tokens with rotation
    token_data = {
        "sub": str(user.id),
        "role": user.user_role,
        "userName": user.user_name,
        "orgId": user.org_id,
        "version": user.token_version
    }
    
    new_access_token = create_access_token(token_data, jti=new_access_jti)
    new_refresh_token = create_refresh_token(token_data, jti=new_refresh_jti)
    
    # Set new tokens as httpOnly cookies
    set_token_cookies(
        response,
        new_access_token,
        new_refresh_token,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    # Create new session for the new access token
    try:
        session_service.create_session(
            user_id=user.id,
            jti=new_access_jti,
            device_info=device_info,
            ip_address=client_ip,
            user_agent=user_agent,
            fingerprint=fingerprint
        )
    except Exception as e:
        # If session creation fails, log but continue
        print(f"Session creation error: {e}")
    
    # Log token refresh
    await SecurityAuditLogger.log_security_event(
        SecurityAuditLogger.EVENT_TOKEN_REFRESH,
        user.id,
        client_ip,
        user_agent
    )
    
    return {
        "success": True,
        "message": "Token refreshed successfully"
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user with proper session termination
    
    Features:
    - Blacklists current access token
    - Removes active session from Redis
    - Prevents token reuse
    - Clears httpOnly cookies
    """
    # Get token from cookie
    token = request.cookies.get("access_token")
    
    if token:
        payload = decode_token(token)
        
        if payload:
            jti = payload.get("jti")
            if jti:
                # Calculate remaining TTL for blacklist
                expiry = get_token_expiry(payload)
                if expiry:
                    remaining_seconds = int((expiry - datetime.utcnow()).total_seconds())
                    if remaining_seconds > 0:
                        # Blacklist the token
                        session_service.blacklist_token(jti, ttl=remaining_seconds)
                
                # Remove session
                session_service.revoke_session(current_user.id, jti)
    
    # Clear token cookies
    clear_token_cookies(response)
    
    # Log logout
    await SecurityAuditLogger.log_security_event(
        SecurityAuditLogger.EVENT_LOGOUT,
        current_user.id,
        get_client_ip(request),
        request.headers.get("user-agent")
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user's information"""
    return {
        "id": current_user.id,
        "userName": current_user.user_name,
        "examinerId": current_user.examiner_id,
        "userRole": current_user.user_role.lower(),
        "orgId": current_user.org_id,
        "passwordLastChanged": current_user.password_last_changed.isoformat() if current_user.password_last_changed else None,
        "mustChangePassword": current_user.must_change_password if current_user.must_change_password else False,
        "lastLogin": current_user.last_login.isoformat() if current_user.last_login else None,
        "isActive": current_user.is_active,
        "createdAt": current_user.created_at.isoformat() if current_user.created_at else None,
        "modifiedAt": current_user.modified_at.isoformat() if current_user.modified_at else None
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    req: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password with automatic token invalidation
    
    All users can change their own password by providing their current password.
    No approval workflow - password changes are immediate.
    
    Security Features:
    - Invalidates all existing tokens (increments token_version)
    - Revokes all active sessions
    - User must login again with new password
    """
    # Verify current password first
    if not verify_password(request.old_password, current_user.password_hash):
        # Log failed password change
        await SecurityAuditLogger.log_security_event(
            SecurityAuditLogger.EVENT_PASSWORD_CHANGE_FAILED,
            current_user.id,
            get_client_ip(req),
            req.headers.get("user-agent"),
            {"reason": "incorrect_old_password"}
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Check if new password is same as current
    if verify_password(request.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Validate new password (minimum 8 characters)
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(request.new_password)
    current_user.password_last_changed = datetime.utcnow()
    current_user.must_change_password = False  # Clear the flag if it was set
    current_user.modified_at = datetime.utcnow()
    
    # Increment token version to invalidate all existing tokens
    current_user.token_version += 1
    
    db.commit()
    
    # Revoke all user sessions in Redis
    revoked_count = session_service.revoke_all_user_sessions(current_user.id)
    
    # Log successful password change
    await SecurityAuditLogger.log_security_event(
        SecurityAuditLogger.EVENT_PASSWORD_CHANGE,
        current_user.id,
        get_client_ip(req),
        req.headers.get("user-agent")
    )
    
    return {
        "message": "Password changed successfully. All active sessions have been terminated. Please login again.",
        "sessionsRevoked": revoked_count
    }


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, req: Request, db: Session = Depends(get_db)):
    """Request password reset"""
    import secrets
    
    user = db.query(User).filter(User.user_name == request.user_name).first()
    
    if not user:
        return {"message": "If the username exists, a reset link will be sent"}
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    token_hash = get_password_hash(token)
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    
    db.add(reset_token)
    db.commit()
    
    # Log password reset request
    await SecurityAuditLogger.log_security_event(
        SecurityAuditLogger.EVENT_PASSWORD_RESET_REQUEST,
        user.id,
        get_client_ip(req),
        req.headers.get("user-agent")
    )
    
    # TODO: Send email with reset link
    return {
        "message": "If the username exists, a reset link will be sent",
        "token": token  # Remove in production
    }


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, req: Request, db: Session = Depends(get_db)):
    """Reset password using reset token"""
    reset_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.expires_at > datetime.utcnow(),
        PasswordResetToken.used_at.is_(None)
    ).all()
    
    valid_token = None
    for rt in reset_tokens:
        if verify_password(request.token, rt.token):
            valid_token = rt
            break
    
    if not valid_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = db.query(User).filter(User.id == valid_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.password_hash = get_password_hash(request.new_password)
    user.password_last_changed = datetime.utcnow()
    user.modified_at = datetime.utcnow()
    valid_token.used_at = datetime.utcnow()
    
    db.commit()
    
    # Log password reset
    await SecurityAuditLogger.log_security_event(
        SecurityAuditLogger.EVENT_PASSWORD_RESET,
        user.id,
        get_client_ip(req),
        req.headers.get("user-agent")
    )
    
    return {"message": "Password reset successfully"}


# ============ Session Management Endpoints ============

@router.get("/sessions", response_model=SessionListResponse)
async def get_active_sessions(current_user: User = Depends(get_current_active_user)):
    """
    Get all active sessions for the current user
    
    Returns list of all active sessions with device info, IP, and last activity
    """
    sessions = session_service.get_user_sessions(current_user.id)
    
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


@router.delete("/sessions/{session_id}")
async def revoke_specific_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Revoke a specific session (logout from specific device)
    
    Args:
        session_id: Session ID to revoke
    
    Returns:
        Success message
    """
    # Verify session belongs to current user
    session = session_service.get_session(current_user.id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Revoke the session
    success = session_service.revoke_session(current_user.id, session_id)
    
    if success:
        # Log session revocation
        await SecurityAuditLogger.log_security_event(
            SecurityAuditLogger.EVENT_SESSION_REVOKED,
            current_user.id,
            get_client_ip(request),
            request.headers.get("user-agent"),
            {"session_id": session_id}
        )
        
        return {"message": "Session revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


@router.delete("/sessions", response_model=RevokeAllSessionsResponse)
async def revoke_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Revoke all sessions except current one (logout from all other devices)
    
    Note: This will invalidate all tokens, requiring login on all devices
    """
    # Revoke all sessions
    revoked_count = session_service.revoke_all_user_sessions(current_user.id)
    
    # Log session revocation
    await SecurityAuditLogger.log_security_event(
        SecurityAuditLogger.EVENT_ALL_SESSIONS_REVOKED,
        current_user.id,
        get_client_ip(request),
        request.headers.get("user-agent"),
        {"sessions_revoked": revoked_count}
    )
    
    return {
        "message": f"All {revoked_count} sessions have been revoked. You will need to login again on all devices.",
        "sessionsRevoked": revoked_count
    }
