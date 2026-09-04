"""Pydantic schemas for authentication requests, JWT tokens, and user representations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Credentials payload for authentication login."""

    username: str = Field(
        ...,
        description="Username or registered email address",
        min_length=1,
        max_length=100,
        examples=["admin", "officer@rakshakgis.gov.in"],
    )
    password: str = Field(
        ...,
        description="Account password",
        min_length=1,
        examples=["secret_password_123"],
    )


class TokenResponse(BaseModel):
    """JWT bearer access token response payload."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token type designation")
    expires_in: int = Field(..., description="Token validity window in seconds")


class UserRead(BaseModel):
    """Public, sanitized representation of an authenticated user (passwords omitted)."""

    id: int = Field(..., description="Unique user ID")
    username: str = Field(..., description="Unique system username")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="Full legal / official name")
    role: str = Field(..., description="Assigned governance role")
    department: Optional[str] = Field(None, description="Administrative department or agency")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Account last update timestamp")

    model_config = ConfigDict(from_attributes=True)
