"""Standardized common API schemas, error models, and response envelopes."""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured details of an API error occurrence."""

    code: str = Field(
        ...,
        description="Stable machine-readable error code (e.g. NOT_FOUND, VALIDATION_ERROR).",
        examples=["NOT_FOUND"],
    )
    message: str = Field(
        ...,
        description="Human-readable description of the error.",
        examples=["The requested resource was not found."],
    )
    status_code: int = Field(
        ...,
        description="HTTP status code associated with the error.",
        examples=[404],
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request correlation identifier.",
        examples=["req-6b2a0c4f8d1e4b2a8d1e4b2a0c4f8d1e"],
    )
    details: Optional[Any] = Field(
        default=None,
        description="Optional structured contextual details (e.g. field-level validation errors).",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the error occurred.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class ErrorResponse(BaseModel):
    """Standardized top-level API error response contract."""

    success: bool = Field(
        default=False,
        description="Always False for error responses.",
        examples=[False],
    )
    error: ErrorDetail = Field(
        ...,
        description="Detailed structured error information.",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "status_code": 404,
                    "request_id": "req-6b2a0c4f8d1e4b2a8d1e4b2a0c4f8d1e",
                    "details": None,
                    "timestamp": "2026-09-04T11:00:00Z",
                },
            }
        },
    )


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard response envelope for successful API operations."""

    success: bool = Field(
        default=True,
        description="Always True for successful responses.",
        examples=[True],
    )
    data: T = Field(
        ...,
        description="Payload returned by the endpoint.",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request correlation identifier.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the response.",
    )


class PaginationMetadata(BaseModel):
    """Metadata describing a paginated collection."""

    total: int = Field(..., description="Total count of items across all pages.", ge=0)
    page: int = Field(..., description="Current page number (1-indexed).", ge=1)
    page_size: int = Field(..., description="Number of items per page.", ge=1)
    total_pages: int = Field(..., description="Total number of available pages.", ge=0)
    has_next: bool = Field(..., description="True if a subsequent page is available.")
    has_prev: bool = Field(..., description="True if a preceding page is available.")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized response container for paginated collections."""

    success: bool = Field(default=True, description="Always True for successful responses.")
    data: List[T] = Field(..., description="List of items for the requested page.")
    pagination: PaginationMetadata = Field(..., description="Pagination navigation metadata.")
    request_id: Optional[str] = Field(default=None, description="Unique request correlation identifier.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the response.",
    )
