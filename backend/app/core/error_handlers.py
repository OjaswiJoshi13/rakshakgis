"""Centralized FastAPI exception handlers enforcing the standardized API error contract."""

import http
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.middleware import REQUEST_ID_HEADER, get_request_id
from app.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger("rakshakgis.errors")

_HTTP_STATUS_CODE_MAP: Dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    406: "NOT_ACCEPTABLE",
    408: "REQUEST_TIMEOUT",
    409: "CONFLICT",
    410: "GONE",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_SERVER_ERROR",
    501: "NOT_IMPLEMENTED",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
}


def _resolve_request_id(request: Request) -> Optional[str]:
    """Retrieve request ID from request state or context variable."""
    return getattr(request.state, "request_id", None) or get_request_id()


def _format_validation_errors(raw_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format raw Pydantic validation errors into a clean, client-friendly structure."""
    formatted: List[Dict[str, Any]] = []
    for err in raw_errors:
        loc = err.get("loc", ())
        # Filter out root body marker for cleaner field paths
        field_path = ".".join(str(part) for part in loc if part != "body")
        formatted.append(
            {
                "field": field_path or "root",
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )
    return formatted


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application and domain exceptions."""
    request_id = _resolve_request_id(request)
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
            details=exc.details,
        ),
    )
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(mode="json"),
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard Starlette / FastAPI HTTPExceptions."""
    request_id = _resolve_request_id(request)
    code = _HTTP_STATUS_CODE_MAP.get(
        exc.status_code,
        f"HTTP_{exc.status_code}",
    )
    message = str(exc.detail) if exc.detail else http.HTTPStatus(exc.status_code).phrase

    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=code,
            message=message,
            status_code=exc.status_code,
            request_id=request_id,
            details=None,
        ),
    )
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    if exc.headers:
        if headers is None:
            headers = {}
        headers.update(exc.headers)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(mode="json"),
        headers=headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI / Pydantic request validation errors."""
    request_id = _resolve_request_id(request)
    formatted_details = _format_validation_errors(exc.errors())

    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed. Please check the supplied parameters.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            request_id=request_id,
            details=formatted_details,
        ),
    )
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload.model_dump(mode="json"),
        headers=headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected internal exceptions, sanitizing client responses."""
    request_id = _resolve_request_id(request)
    logger.exception(
        "Unhandled exception processing request [request_id=%s] %s %s: %s",
        request_id,
        request.method,
        request.url.path,
        exc,
    )

    # Safe generic message: internal details, stack traces, and database errors are never leaked
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
            details=None,
        ),
    )
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(mode="json"),
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all centralized exception handlers with the FastAPI application instance."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
