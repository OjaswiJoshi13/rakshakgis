"""RakshakGIS Backend Application Entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.database import check_db_readiness
from app.core.error_handlers import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.schemas.common import ErrorResponse

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
    if settings.APP_ENV == "development" and settings.DATA_MODE == "demo":
        try:
            from app.core.database import SessionLocal
            from app.data.seed import seed_himalayan_pilot_data

            db = SessionLocal()
            try:
                seed_himalayan_pilot_data(db)
            finally:
                db.close()
        except Exception as e:
            logger.warning("Development demo seeding encountered an issue during startup: %s", e)

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
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Resource Not Found"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)

# Register request correlation ID middleware
app.add_middleware(RequestIDMiddleware)

# Configure CORS for local development
# Configure CORS for local development
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=(
            r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"
            if settings.APP_ENV == "development"
            else None
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register centralized exception handlers for standard error contract
register_error_handlers(app)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"], include_in_schema=False)
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
