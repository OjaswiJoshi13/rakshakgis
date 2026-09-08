"""Automated tests for authentication, password hashing, JWT operations, RBAC, and protected endpoints."""

from datetime import timedelta
import time
import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import UserRole, get_current_user, require_roles
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.middleware import REQUEST_ID_HEADER
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.main import app
from app.models.governance import User

# Test router to exercise RBAC dependencies on protected routes
mock_auth_router = APIRouter(prefix="/test-rbac", tags=["Testing"])


@mock_auth_router.get("/admin-only")
def route_admin_only(user: User = Depends(require_roles(UserRole.ADMIN))):
    return {"status": "ok", "user": user.username, "role": user.role}


@mock_auth_router.get("/officer-or-admin")
def route_officer_or_admin(
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRICT_OFFICER))
):
    return {"status": "ok", "user": user.username, "role": user.role}


@mock_auth_router.get("/responder-only")
def route_responder_only(user: User = Depends(require_roles(UserRole.FIELD_RESPONDER))):
    return {"status": "ok", "user": user.username, "role": user.role}


@mock_auth_router.get("/authenticated-any")
def route_authenticated_any(user: User = Depends(get_current_user)):
    return {"status": "ok", "user": user.username, "role": user.role}


app.include_router(mock_auth_router)


@pytest.fixture(scope="module")
def db_session():
    """Provide a database session for test user management and cleanup."""
    session = SessionLocal()
    try:
        # Pre-cleanup in case of leftovers
        session.query(User).filter(User.username.like("test_auth_%")).delete(
            synchronize_session=False
        )
        session.commit()
        yield session
    finally:
        session.query(User).filter(User.username.like("test_auth_%")).delete(
            synchronize_session=False
        )
        session.commit()
        session.close()


@pytest.fixture(scope="module")
def seed_users(db_session: Session):
    """Seed users with distinct roles and active/inactive states for authentication testing."""
    password_plain = "Rakshak@2026Secure!"
    password_hash = hash_password(password_plain)

    users = {
        "admin": User(
            username="test_auth_admin",
            email="test_auth_admin@rakshakgis.gov.in",
            hashed_password=password_hash,
            full_name="Admin Officer",
            role="admin",
            department="State Disaster Management Authority",
            is_active=True,
        ),
        "district_officer": User(
            username="test_auth_officer",
            email="test_auth_officer@rakshakgis.gov.in",
            hashed_password=password_hash,
            full_name="District Collector Chamoli",
            role="district_officer",
            department="District Administration",
            is_active=True,
        ),
        "field_responder": User(
            username="test_auth_responder",
            email="test_auth_responder@rakshakgis.gov.in",
            hashed_password=password_hash,
            full_name="Field Team Lead",
            role="field_responder",
            department="Emergency Response Force",
            is_active=True,
        ),
        "viewer": User(
            username="test_auth_viewer",
            email="test_auth_viewer@rakshakgis.gov.in",
            hashed_password=password_hash,
            full_name="Public Observer",
            role="viewer",
            department=None,
            is_active=True,
        ),
        "inactive": User(
            username="test_auth_inactive",
            email="test_auth_inactive@rakshakgis.gov.in",
            hashed_password=password_hash,
            full_name="Deactivated Account",
            role="viewer",
            department=None,
            is_active=False,
        ),
    }

    for u in users.values():
        db_session.add(u)
    db_session.commit()
    for u in users.values():
        db_session.refresh(u)

    return {
        "users": users,
        "password": password_plain,
    }


# ==============================================================================
# 1. Password Hashing & Verification Tests
# ==============================================================================


def test_password_hashing_and_verification():
    """Verify password hashing produces distinct bcrypt hashes and verifies accurately."""
    raw = "MySuperSecretPassword@123"
    hashed = hash_password(raw)

    assert hashed != raw
    assert hashed.startswith("$2b$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_password_hash_uniqueness():
    """Verify bcrypt generates unique salts for identical plaintext passwords."""
    raw = "SamePassword"
    hash1 = hash_password(raw)
    hash2 = hash_password(raw)
    assert hash1 != hash2
    assert verify_password(raw, hash1) is True
    assert verify_password(raw, hash2) is True


# ==============================================================================
# 2. JWT Generation, Expiration, and Validation Tests
# ==============================================================================


def test_jwt_generation_and_decoding():
    """Verify access token creation and decoding with claims."""
    token = create_access_token(
        subject=42,
        claims={"username": "agent007", "role": "admin"},
        expires_delta=timedelta(minutes=15),
    )
    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["username"] == "agent007"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_token():
    """Verify expired JWTs are rejected when validated."""
    expired_token = create_access_token(
        subject=100,
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )
    with pytest.raises(Exception):
        decode_access_token(expired_token)


def test_jwt_secret_is_configuration_driven():
    """Verify JWT secret is pulled dynamically from application settings."""
    settings = get_settings()
    assert settings.JWT_SECRET is not None
    assert len(settings.JWT_SECRET) > 0
    assert settings.JWT_ALGORITHM == "HS256"


def test_jwt_secret_production_validation():
    """Verify that placeholder or empty JWT secrets are rejected in production environment."""
    from app.core.config import Settings

    with pytest.raises(ValueError, match="JWT_SECRET.*mandatory in production"):
        Settings(APP_ENV="production", JWT_SECRET="replace_with_a_secure_random_jwt_secret_in_production")

    with pytest.raises(ValueError, match="JWT_SECRET.*mandatory in production"):
        Settings(APP_ENV="production", JWT_SECRET="")

    # Custom valid production secret succeeds
    prod_settings = Settings(APP_ENV="production", JWT_SECRET="actual_high_entropy_prod_secret_987654321")
    assert prod_settings.JWT_SECRET == "actual_high_entropy_prod_secret_987654321"


# ==============================================================================
# 3. Login Endpoint Tests
# ==============================================================================


def test_login_success_with_username(client: TestClient, seed_users: dict):
    """Verify login succeeds using username and returns Bearer token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test_auth_admin", "password": seed_users["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert REQUEST_ID_HEADER in response.headers


def test_login_success_with_email(client: TestClient, seed_users: dict):
    """Verify login succeeds using email address."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test_auth_officer@rakshakgis.gov.in", "password": seed_users["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient):
    """Verify login fails with wrong password and returns standardized 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test_auth_admin", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "password" not in data["error"]["message"].lower() or "invalid" in data["error"]["message"].lower()


def test_login_nonexistent_user(client: TestClient):
    """Verify login fails for nonexistent user and does not leak account presence."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent_user_xyz", "password": "AnyPassword123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_login_inactive_user(client: TestClient, seed_users: dict):
    """Verify inactive account cannot authenticate and returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test_auth_inactive", "password": seed_users["password"]},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "inactive" in data["error"]["message"].lower()


# ==============================================================================
# 4. Current User Endpoint (/api/v1/auth/me) Tests
# ==============================================================================


def test_get_me_success_and_no_password_leakage(client: TestClient, seed_users: dict):
    """Verify /me returns authenticated user details and strictly omits password hash."""
    user = seed_users["users"]["admin"]
    token = create_access_token(subject=user.id)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
    assert data["role"] == "admin"
    assert data["department"] == user.department
    assert data["is_active"] is True

    # Security check: Password hash MUST never be present
    assert "hashed_password" not in data
    assert "password" not in data
    assert "hashed_password" not in response.text


def test_get_me_unauthenticated(client: TestClient):
    """Verify /me without authorization header returns 401 UNAUTHORIZED."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert REQUEST_ID_HEADER in response.headers


# ==============================================================================
# 5. Token Validation Error Cases Tests
# ==============================================================================


def test_token_malformed(client: TestClient):
    """Verify malformed tokens return 401 UNAUTHORIZED."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_token_expired(client: TestClient, seed_users: dict):
    """Verify expired token returns 401 with appropriate message."""
    user = seed_users["users"]["admin"]
    token = create_access_token(subject=user.id, expires_delta=timedelta(seconds=-10))

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "expired" in data["error"]["message"].lower()


def test_token_invalid_signature(client: TestClient, seed_users: dict):
    """Verify token signed with different secret key is rejected with 401."""
    import jwt
    user = seed_users["users"]["admin"]
    fake_token = jwt.encode(
        {"sub": str(user.id), "iat": int(time.time()), "exp": int(time.time()) + 3600, "type": "access"},
        "completely_wrong_secret_key_12345",
        algorithm="HS256",
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_token_missing_sub_claim(client: TestClient):
    """Verify token without 'sub' claim returns 401."""
    import jwt
    settings = get_settings()
    token = jwt.encode(
        {"iat": int(time.time()), "exp": int(time.time()) + 3600, "type": "access"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_token_wrong_type_claim(client: TestClient, seed_users: dict):
    """Verify non-access token (e.g., refresh token) is rejected."""
    import jwt
    settings = get_settings()
    user = seed_users["users"]["admin"]
    token = jwt.encode(
        {"sub": str(user.id), "iat": int(time.time()), "exp": int(time.time()) + 3600, "type": "refresh"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_token_nonexistent_user(client: TestClient):
    """Verify valid token with non-existent user ID in database returns 401."""
    token = create_access_token(subject=999999)  # User does not exist
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_token_inactive_user_rejected(client: TestClient, seed_users: dict):
    """Verify valid token for inactive user returns 401."""
    user = seed_users["users"]["inactive"]
    token = create_access_token(subject=user.id)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert "inactive" in response.json()["error"]["message"].lower()


# ==============================================================================
# 6. Role-Based Access Control (RBAC) Tests
# ==============================================================================


def test_rbac_admin_access_admin_route(client: TestClient, seed_users: dict):
    """Verify admin role is authorized for admin-only endpoint."""
    user = seed_users["users"]["admin"]
    token = create_access_token(subject=user.id)

    response = client.get(
        "/test-rbac/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["user"] == user.username


def test_rbac_officer_denied_admin_route(client: TestClient, seed_users: dict):
    """Verify district officer is denied (HTTP 403 FORBIDDEN) on admin-only endpoint."""
    user = seed_users["users"]["district_officer"]
    token = create_access_token(subject=user.id)

    response = client.get(
        "/test-rbac/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"
    assert data["error"]["status_code"] == 403
    assert REQUEST_ID_HEADER in response.headers


def test_rbac_multi_role_allowance(client: TestClient, seed_users: dict):
    """Verify route allowing multiple roles permits both admin and district officer."""
    admin = seed_users["users"]["admin"]
    officer = seed_users["users"]["district_officer"]
    viewer = seed_users["users"]["viewer"]

    # Admin -> Allowed
    token_admin = create_access_token(subject=admin.id)
    r_admin = client.get("/test-rbac/officer-or-admin", headers={"Authorization": f"Bearer {token_admin}"})
    assert r_admin.status_code == 200

    # District Officer -> Allowed
    token_officer = create_access_token(subject=officer.id)
    r_officer = client.get("/test-rbac/officer-or-admin", headers={"Authorization": f"Bearer {token_officer}"})
    assert r_officer.status_code == 200

    # Viewer -> Forbidden 403
    token_viewer = create_access_token(subject=viewer.id)
    r_viewer = client.get("/test-rbac/officer-or-admin", headers={"Authorization": f"Bearer {token_viewer}"})
    assert r_viewer.status_code == 403
    assert r_viewer.json()["error"]["code"] == "FORBIDDEN"


def test_rbac_unauthenticated_returns_401(client: TestClient):
    """Verify accessing role-protected route without token returns 401 UNAUTHORIZED, not 403."""
    response = client.get("/test-rbac/admin-only")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


# ==============================================================================
# 7. OpenAPI & Documentation Verification
# ==============================================================================


def test_openapi_documents_auth_endpoints(client: TestClient):
    """Verify OpenAPI schema documents /api/v1/auth/login and /api/v1/auth/me."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    paths = schema.get("paths", {})
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "post" in paths["/api/v1/auth/login"]
    assert "get" in paths["/api/v1/auth/me"]

    # Schemas
    components = schema.get("components", {}).get("schemas", {})
    assert "LoginRequest" in components
    assert "TokenResponse" in components
    assert "UserRead" in components
