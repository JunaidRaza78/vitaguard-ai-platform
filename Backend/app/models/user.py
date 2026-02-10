"""
User Model
Database model for user authentication and profile
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4


class User(BaseModel):
    """User database model"""

    user_id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    username: str
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None

    # Account status
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # Security
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None

    # Profile
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "timezone": "America/New_York",
                "language": "en"
            }
        }


class RefreshToken(BaseModel):
    """Refresh token model for token rotation"""

    token_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    device_info: Optional[str] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class LoginAttempt(BaseModel):
    """Login attempt tracking for security"""

    attempt_id: UUID = Field(default_factory=uuid4)
    email: str
    ip_address: str
    user_agent: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None
    attempted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class Session(BaseModel):
    """User session model"""

    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    access_token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True
