"""Authentication endpoints for user login, JWT issuance, and current-user retrieval."""

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.models.governance import User
from app.schemas.auth import LoginRequest, TokenResponse, UserRead

auth_router = APIRouter(tags=["Authentication"])
settings = get_settings()


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login & Token Issuance",
    description="Authenticate with username or email and password to receive a JWT access token.",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate credentials and issue a signed JWT access token."""
    identifier = payload.username.strip()

    # Allow login with either username or registered email
    user = (
        db.query(User)
        .filter(or_(User.username == identifier, User.email == identifier))
        .first()
    )

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Invalid username or password.")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive.")

    token = create_access_token(
        subject=user.id,
        claims={"username": user.username, "role": user.role},
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.get(
    "/me",
    response_model=UserRead,
    summary="Get Current Authenticated User",
    description="Retrieve account profile of currently authenticated user without sensitive credentials.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Return profile representation of the authenticated user."""
    return UserRead.model_validate(current_user)
