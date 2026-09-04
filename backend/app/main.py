"""RakshakGIS Backend Application Entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.database import check_db_readiness
from app.core.logging import setup_logging

settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    logger.info(
        "Starting %s v%s (environment: %s, data_mode: %s)",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.APP_ENV,
        settings.DATA_MODE,
    )
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS for local development
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """Process health check endpoint (independent of database connectivity)."""
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "data_mode": settings.DATA_MODE,
        "version": settings.VERSION,
    }


@app.get("/ready", tags=["Health"])
def readiness_check(response: Response) -> dict:
    """Service readiness endpoint verifying database and PostGIS connectivity."""
    readiness = check_db_readiness()
    if readiness.get("status") != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return readiness


@app.get("/", tags=["System"])
def root() -> dict:
    """Root application informational endpoint."""
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/docs",
        "api_v1_url": settings.API_V1_STR,
    }


# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)
