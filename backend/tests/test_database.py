"""Automated tests for PostgreSQL and PostGIS database engine setup."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, check_db_readiness, engine, get_db
from app.main import app


def test_database_settings_configuration():
    """Verify database configuration loads with expected attributes."""
    settings = get_settings()
    assert settings.POSTGRES_DB == "rakshakgis"
    assert settings.POSTGRES_USER == "rakshak"
    assert settings.POSTGRES_PORT == 5432
    assert settings.DATABASE_URL != ""
    assert "postgresql://" in settings.DATABASE_URL


def test_engine_and_session_factory_initialization():
    """Verify SQLAlchemy engine and session factory are initialized without immediate connection."""
    assert engine is not None
    assert SessionLocal is not None
    assert Base is not None
    assert engine.pool is not None


def test_get_db_dependency_lifecycle():
    """Verify get_db generator yields a session and properly closes it."""
    generator = get_db()
    db = next(generator)
    assert isinstance(db, Session)
    # Complete generator lifecycle
    try:
        next(generator)
    except StopIteration:
        pass


def test_postgresql_live_connection_and_version():
    """Verify live PostgreSQL connectivity and fetch PostgreSQL version."""
    with SessionLocal() as session:
        result = session.execute(text("SELECT version();")).scalar()
        assert result is not None
        assert "PostgreSQL 16" in str(result)


def test_postgis_extension_and_spatial_version():
    """Verify PostGIS extension is loaded and capable of executing spatial functions."""
    with SessionLocal() as session:
        # Check PostGIS version
        postgis_ver = session.execute(text("SELECT PostGIS_Version();")).scalar()
        assert postgis_ver is not None
        assert "3.4" in str(postgis_ver)

        # Check PostGIS full version details (GEOS, PROJ)
        full_ver = session.execute(text("SELECT PostGIS_Full_Version();")).scalar()
        assert full_ver is not None
        assert "POSTGIS" in str(full_ver)
        assert "GEOS" in str(full_ver)
        assert "PROJ" in str(full_ver)

        # Simple harmless spatial capability query (e.g., ST_Point geometry construction)
        geom_wkt = session.execute(
            text("SELECT ST_AsText(ST_SetSRID(ST_Point(77.2090, 28.6139), 4326));")
        ).scalar()
        assert geom_wkt == "POINT(77.209 28.6139)"


def test_check_db_readiness_helper():
    """Verify check_db_readiness returns structured readiness dictionary."""
    readiness = check_db_readiness()
    assert readiness["status"] == "ready"
    assert readiness["database"] == "connected"
    assert "PostgreSQL" in readiness["postgres_version"]
    assert "POSTGIS" in readiness["postgis_version"]


def test_api_ready_endpoint(client: TestClient):
    """Verify GET /ready returns HTTP 200 and valid database readiness payload."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "postgres_version" in data
    assert "postgis_version" in data
