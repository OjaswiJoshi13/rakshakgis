"""Application exception hierarchy for RakshakGIS."""

from typing import Any, Optional


class AppException(Exception):
    """Base application exception for all domain and API errors."""

    default_message: str = "An application error occurred."
    default_status_code: int = 500
    default_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        self.message = message or self.default_message
        self.status_code = status_code if status_code is not None else self.default_status_code
        self.code = code or self.default_code
        self.details = details
        super().__init__(self.message)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"code='{self.code}', "
            f"status_code={self.status_code}, "
            f"message='{self.message}')>"
        )


class BadRequestError(AppException):
    """Exception raised when client sends an invalid or malformed request."""

    default_message = "Bad request."
    default_status_code = 400
    default_code = "BAD_REQUEST"


class ValidationError(AppException):
    """Exception raised when domain or business validation fails."""

    default_message = "Validation error."
    default_status_code = 422
    default_code = "VALIDATION_ERROR"


class UnauthorizedError(AppException):
    """Exception raised when authentication is missing or invalid."""

    default_message = "Authentication credentials were not provided or are invalid."
    default_status_code = 401
    default_code = "UNAUTHORIZED"


class ForbiddenError(AppException):
    """Exception raised when user does not have permission for the requested action."""

    default_message = "You do not have permission to perform this action."
    default_status_code = 403
    default_code = "FORBIDDEN"


class NotFoundError(AppException):
    """Exception raised when a requested resource is not found."""

    default_message = "The requested resource was not found."
    default_status_code = 404
    default_code = "NOT_FOUND"


class ConflictError(AppException):
    """Exception raised when an operation conflicts with the current state of a resource."""

    default_message = "Resource state conflict."
    default_status_code = 409
    default_code = "CONFLICT"


class UnprocessableEntityError(AppException):
    """Exception raised when request parameters are syntactically valid but semantically unprocessable."""

    default_message = "The request could not be processed due to semantic errors."
    default_status_code = 422
    default_code = "UNPROCESSABLE_ENTITY"


class ServiceUnavailableError(AppException):
    """Exception raised when an upstream or internal dependency is temporarily unavailable."""

    default_message = "The service is temporarily unavailable. Please try again later."
    default_status_code = 503
    default_code = "SERVICE_UNAVAILABLE"


class InternalServerError(AppException):
    """Exception raised for unexpected internal server errors."""

    default_message = "An unexpected internal server error occurred."
    default_status_code = 500
    default_code = "INTERNAL_SERVER_ERROR"
