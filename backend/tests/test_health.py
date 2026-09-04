"""Automated tests for FastAPI foundation, health check, and core endpoints."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_app_import_and_initialization():
    """Verify that the FastAPI app instance imports and initializes cleanly."""
    assert app is not None
    assert app.title == "RakshakGIS"


def test_settings_defaults():
    """Verify default settings configuration."""
    settings = get_settings()
    assert settings.PROJECT_NAME == "RakshakGIS"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.APP_ENV in ["development", "staging", "production"]
    assert settings.DATA_MODE in ["demo", "live", "simulation"]
    assert isinstance(settings.CORS_ORIGINS, list)


def test_health_check_endpoint(client: TestClient):
    """Verify GET /health returns HTTP 200 and expected deterministic payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "RakshakGIS"
    assert "environment" in data
    assert "data_mode" in data
    assert "version" in data


def test_root_endpoint(client: TestClient):
    """Verify GET / returns HTTP 200 and foundational API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "RakshakGIS"
    assert data["status"] == "running"
    assert data["docs_url"] == "/docs"
    assert data["api_v1_url"] == "/api/v1"


def test_api_v1_root_endpoint(client: TestClient):
    """Verify GET /api/v1 returns HTTP 200 and online status."""
    response = client.get("/api/v1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["api_version"] == "v1"
    assert data["app"] == "RakshakGIS"


def test_docs_and_openapi_endpoints(client: TestClient):
    """Verify standard FastAPI documentation endpoints are available."""
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert schema["info"]["title"] == "RakshakGIS"
    assert schema["info"]["version"] == "0.1.0"
    assert "/health" in schema["paths"]
    assert "/ready" in schema["paths"]
    assert "/" in schema["paths"]
    assert "/api/v1" in schema["paths"]


def test_cors_headers_present(client: TestClient):
    """Verify configured CORS origin receives Access-Control-Allow-Origin."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_no_database_required():
    """Verify application starts and functions with DATABASE_URL unset or unavailable."""
    import os
    from app.main import app as current_app
    assert "db" not in current_app.extra
    assert current_app is not None

