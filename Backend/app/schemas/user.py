"""
User Schemas
Pydantic schemas for user management and authentication
"""
from pydantic import BaseModel, Field, ConfigDict, field_serializer, field_validator
from typing import Optional, List
from datetime import datetime
import re


def validate_user_name(value: str) -> str:
    """
    Validate and normalize a username:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces into one
    - Allow letters (including capitals), spaces, dots, and hyphens
    - Capitalize the first letter
    - Must be at least 2 characters
    """
    if not value or not value.strip():
        raise ValueError("Username cannot be empty")
    
    # Strip and collapse multiple spaces into one
    value = re.sub(r'\s+', ' ', value.strip())
    
    if len(value) < 2:
        raise ValueError("Username must be at least 2 characters")
    
    # Allow letters, spaces, dots, hyphens, and digits
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9 .\-]*$', value):
        raise ValueError("Username must start with a letter and can contain letters, numbers, spaces, dots, and hyphens")
    
    # Capitalize the first letter
    value = value[0].upper() + value[1:]
    
    return value


# ============ User Schemas ============
class UserBase(BaseModel):
    user_name: str = Field(..., max_length=100, serialization_alias="userName")
    examiner_id: str = Field(..., max_length=50, serialization_alias="examinerId")
    user_role: str = Field(..., serialization_alias="userRole")
    org_id: Optional[int] = Field(None, serialization_alias="orgId")
    
    model_config = ConfigDict(populate_by_name=True)


class UserCreate(BaseModel):
    user_name: str = Field(..., max_length=100, alias="userName")
    examiner_id: str = Field(..., max_length=50, alias="examinerId")  # Required: Manual Employee ID
    password: str = Field(..., min_length=8)
    user_role: str = Field(..., alias="userRole")
    org_id: Optional[int] = Field(None, alias="orgId")
    
    model_config = ConfigDict(populate_by_name=True)

    @field_validator('user_name', mode='before')
    @classmethod
    def normalize_user_name(cls, v: str) -> str:
        return validate_user_name(v)
    
    @field_validator('examiner_id', mode='before')
    @classmethod
    def validate_examiner_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Employee ID is required')
        v = v.strip().upper()
        if len(v) < 2:
            raise ValueError('Employee ID must be at least 2 characters')
        if len(v) > 50:
            raise ValueError('Employee ID must be at most 50 characters')
        # Allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[A-Z0-9_-]+$', v):
            raise ValueError('Employee ID can only contain letters, numbers, hyphens, and underscores')
        return v


class UserUpdate(BaseModel):
    user_name: Optional[str] = Field(None, max_length=100, alias="userName")
    examiner_id: Optional[str] = Field(None, max_length=50, alias="examinerId")
    user_role: Optional[str] = Field(None, alias="userRole")
    org_id: Optional[int] = Field(None, alias="orgId")
    is_active: Optional[bool] = Field(None, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('user_name', mode='before')
    @classmethod
    def normalize_user_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_user_name(v)


class UserResponse(BaseModel):
    id: int
    user_name: str = Field(..., serialization_alias="userName")
    examiner_id: str = Field(..., serialization_alias="examinerId")
    user_role: str = Field(..., serialization_alias="userRole")
    org_id: Optional[int] = Field(None, serialization_alias="orgId")
    password_last_changed: Optional[datetime] = Field(None, serialization_alias="passwordLastChanged")
    must_change_password: bool = Field(default=False, serialization_alias="mustChangePassword")
    last_login: Optional[datetime] = Field(None, serialization_alias="lastLogin")
    is_active: bool = Field(..., serialization_alias="isActive")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    modified_at: datetime = Field(..., serialization_alias="modifiedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)
    
    @field_serializer('user_role')
    def serialize_user_role(self, user_role: str) -> str:
        """Convert user role to lowercase for frontend compatibility"""
        return user_role.lower() if user_role else user_role


class UserWithTeamsResponse(UserResponse):
    """User response with team memberships"""
    teams: List["TeamMembershipResponse"] = []


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int


# ============ Auth Schemas ============
class LoginRequest(BaseModel):
    user_name: str = Field(..., alias="userName")
    password: str

    model_config = ConfigDict(populate_by_name=True)


class LoginResponse(BaseModel):
    """
    Secure login response - tokens are set as httpOnly cookies
    Only user data is returned in the response body
    """
    success: bool = True
    user: UserResponse
    message: str = "Login successful"

    model_config = ConfigDict(populate_by_name=True)


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request - token comes from httpOnly cookie
    This model is kept for backward compatibility but token is extracted from cookie
    """
    refresh_token: Optional[str] = Field(None, alias="refreshToken")

    model_config = ConfigDict(populate_by_name=True)


class RefreshTokenResponse(BaseModel):
    """
    Secure refresh response - tokens are set as httpOnly cookies
    Only success message is returned
    """
    success: bool = True
    message: str = "Token refreshed successfully"

    model_config = ConfigDict(populate_by_name=True)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword")
    new_password: str = Field(..., min_length=8, alias="newPassword")

    model_config = ConfigDict(populate_by_name=True)


class ForgotPasswordRequest(BaseModel):
    user_name: str = Field(..., alias="userName")

    model_config = ConfigDict(populate_by_name=True)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, alias="newPassword")

    model_config = ConfigDict(populate_by_name=True)


class TokenPayload(BaseModel):
    sub: str  # user id
    role: str
    user_name: str = Field(..., alias="userName")
    org_id: Optional[int] = Field(None, alias="orgId")
    exp: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


# ============ Session Management Schemas ============
class SessionResponse(BaseModel):
    """Active session information"""
    session_id: str = Field(serialization_alias="sessionId")
    user_id: int = Field(serialization_alias="userId")
    device_info: str = Field(serialization_alias="deviceInfo")
    ip_address: str = Field(serialization_alias="ipAddress")
    user_agent: str = Field(serialization_alias="userAgent")
    created_at: str = Field(serialization_alias="createdAt")
    last_activity: str = Field(serialization_alias="lastActivity")
    expires_in_seconds: int = Field(serialization_alias="expiresInSeconds")
    
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class SessionListResponse(BaseModel):
    """List of active sessions"""
    sessions: List[SessionResponse]
    total: int


class RevokeSessionRequest(BaseModel):
    """Request to revoke a specific session"""
    session_id: str = Field(..., alias="sessionId")
    
    model_config = ConfigDict(populate_by_name=True)


class RevokeAllSessionsResponse(BaseModel):
    """Response after revoking all sessions"""
    message: str
    sessions_revoked: int = Field(serialization_alias="sessionsRevoked")
    
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


# ============ Team Membership Schema (for circular import resolution) ============
class TeamMembershipResponse(BaseModel):
    """Team membership info embedded in user response"""
    team_id: int = Field(serialization_alias="teamId")
    team_name: str = Field(serialization_alias="teamName")
    role: str
    joined_at: datetime = Field(serialization_alias="joinedAt")
    is_active: bool = Field(serialization_alias="isActive")
    team_is_active: bool = Field(default=True, serialization_alias="teamIsActive")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)


# Update forward reference
UserWithTeamsResponse.model_rebuild()
