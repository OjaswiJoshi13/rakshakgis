"""Reusable FastAPI dependencies for authentication, token extraction, and RBAC authorization."""

from enum import Enum
from typing import Optional, Sequence, Union

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.governance import User

# Optional Bearer scheme to enable OpenAPI security documentation without raising generic 403s
oauth2_scheme = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """Authoritative platform roles aligned with the governance data model."""

    ADMIN = "admin"
    DISTRICT_OFFICER = "district_officer"
    FIELD_RESPONDER = "field_responder"
    VIEWER = "viewer"


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate incoming JWT bearer token and retrieve active user from PostgreSQL."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Authentication credentials were not provided.")

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Authentication token has expired.")
    except jwt.InvalidSignatureError:
        raise UnauthorizedError("Invalid token signature.")
    except (jwt.InvalidTokenError, jwt.DecodeError):
        raise UnauthorizedError("Invalid authentication token.")

    token_type = payload.get("type")
    if token_type != "access":
        raise UnauthorizedError("Invalid token type. Expected access token.")

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise UnauthorizedError("Authentication token missing required subject claim.")

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise UnauthorizedError("Invalid user identity in authentication token.")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError("User associated with token does not exist.")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive.")

    return user


class RoleChecker:
    """Callable dependency enforcing Role-Based Access Control (RBAC)."""

    def __init__(self, allowed_roles: Sequence[Union[UserRole, str]]):
        self.allowed_roles = {
            r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles
        }

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """Verify the authenticated user holds one of the required roles."""
        if current_user.role not in self.allowed_roles:
            raise ForbiddenError(
                message=f"Access forbidden: requires one of the following roles: {', '.join(sorted(self.allowed_roles))}.",
                details={
                    "user_role": current_user.role,
                    "required_roles": sorted(list(self.allowed_roles)),
                },
            )
        return current_user


def require_roles(*roles: Union[UserRole, str]) -> RoleChecker:
    """Factory helper returning a RoleChecker dependency for specified roles."""
    return RoleChecker(roles)
