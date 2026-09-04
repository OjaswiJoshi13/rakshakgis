"""PostgreSQL and PostGIS database engine and session configuration."""

import logging
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import get_settings

logger = logging.getLogger("rakshakgis.database")
settings = get_settings()

# SQLAlchemy Engine configured with connection health checks
# Note: create_engine does not open immediate persistent connections at import time.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory for database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for future ORM models (Chunk M2-03)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a scoped database session for FastAPI request lifecycles."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_readiness(db_session: Optional[Session] = None) -> Dict[str, Any]:
    """Execute non-destructive queries to verify PostgreSQL and PostGIS availability."""
    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True

    try:
        # Verify basic PostgreSQL connectivity and version
        pg_res = db_session.execute(text("SELECT version();")).scalar()
        
        # Verify PostGIS spatial extension availability and version
        postgis_res = db_session.execute(text("SELECT PostGIS_Full_Version();")).scalar()

        return {
            "status": "ready",
            "database": "connected",
            "postgres_version": str(pg_res) if pg_res else "unknown",
            "postgis_version": str(postgis_res) if postgis_res else "unknown",
        }
    except Exception as exc:
        logger.error("Database readiness check failed: %s", exc)
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(exc),
        }
    finally:
        if close_session:
            db_session.close()
