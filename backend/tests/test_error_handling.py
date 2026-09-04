"""Automated tests for common API error handling, exception hierarchy, and request correlation IDs."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.exceptions import (
    AppException,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from app.core.middleware import REQUEST_ID_HEADER
from app.main import app
from app.schemas.common import ErrorResponse

# Ephemeral testing router to exercise exception handlers without polluting production routes
mock_api_router = APIRouter(prefix="/test-common-api", tags=["Testing"])


class PayloadModel(BaseModel):
    name: str = Field(..., min_length=3)
    score: float = Field(..., ge=0.0, le=100.0)


@mock_api_router.get("/app-exception")
def route_app_exception():
    raise AppException(
        message="Base application error occurred.",
        status_code=500,
        code="CUSTOM_APP_ERROR",
        details={"context": "test"},
    )


@mock_api_router.get("/not-found")
def route_not_found():
    raise NotFoundError("Village not found", details={"village_id": 9999})


@mock_api_router.get("/conflict")
def route_conflict():
    raise ConflictError(
        "Village is already allocated to a candidate site.",
        details={"village_id": 101, "existing_site_id": 5},
    )


@mock_api_router.get("/bad-request")
def route_bad_request():
    raise BadRequestError("Malformed query parameters.")


@mock_api_router.get("/validation-error")
def route_validation_error():
    raise ValidationError(
        "Business rule validation failed.",
        details=[{"rule": "slope_threshold", "limit": 45.0, "actual": 52.3}],
    )


@mock_api_router.get("/unauthorized")
def route_unauthorized():
    raise UnauthorizedError()


@mock_api_router.get("/forbidden")
def route_forbidden():
    raise ForbiddenError()


@mock_api_router.get("/service-unavailable")
def route_service_unavailable():
    raise ServiceUnavailableError()


@mock_api_router.get("/unhandled")
def route_unhandled():
    raise RuntimeError(
        "Critical database failure: postgresql://admin:super_secret_password@db:5432/prod; table corrupted"
    )


@mock_api_router.post("/pydantic-validation")
def route_pydantic_validation(payload: PayloadModel):
    return {"status": "ok", "received": payload.name}


# Attach mock router to app for test lifecycle
app.include_router(mock_api_router)


def test_request_id_generated_and_returned_in_header(client: TestClient):
    """Verify that every response receives a generated X-Request-ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert REQUEST_ID_HEADER in response.headers
    assert response.headers[REQUEST_ID_HEADER].startswith("req-")


def test_incoming_request_id_propagated(client: TestClient):
    """Verify that a client-supplied X-Request-ID is accepted and echoed in response headers."""
    custom_id = "test-correlation-abc-123"
    response = client.get("/health", headers={REQUEST_ID_HEADER: custom_id})
    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == custom_id


def test_standard_app_exception_response(client: TestClient):
    """Verify AppException maps to standardized ErrorResponse schema."""
    response = client.get("/test-common-api/app-exception")
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    err = data["error"]
    assert err["code"] == "CUSTOM_APP_ERROR"
    assert err["message"] == "Base application error occurred."
    assert err["status_code"] == 500
    assert err["details"] == {"context": "test"}
    assert err["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert "timestamp" in err


def test_not_found_error_mapping(client: TestClient):
    """Verify NotFoundError returns HTTP 404 with NOT_FOUND code and structured payload."""
    response = client.get("/test-common-api/not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    err = data["error"]
    assert err["code"] == "NOT_FOUND"
    assert err["message"] == "Village not found"
    assert err["status_code"] == 404
    assert err["details"] == {"village_id": 9999}
    assert err["request_id"] is not None


def test_conflict_error_mapping(client: TestClient):
    """Verify ConflictError returns HTTP 409 with CONFLICT code."""
    response = client.get("/test-common-api/conflict")
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    err = data["error"]
    assert err["code"] == "CONFLICT"
    assert err["status_code"] == 409
    assert err["details"]["existing_site_id"] == 5


def test_bad_request_error_mapping(client: TestClient):
    """Verify BadRequestError returns HTTP 400 with BAD_REQUEST code."""
    response = client.get("/test-common-api/bad-request")
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    err = data["error"]
    assert err["code"] == "BAD_REQUEST"
    assert err["status_code"] == 400


def test_validation_error_mapping(client: TestClient):
    """Verify ValidationError returns HTTP 422 with VALIDATION_ERROR code."""
    response = client.get("/test-common-api/validation-error")
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    err = data["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert err["status_code"] == 422
    assert len(err["details"]) == 1


def test_unauthorized_and_forbidden_mappings(client: TestClient):
    """Verify UnauthorizedError (401) and ForbiddenError (403) are properly mapped."""
    r_unauth = client.get("/test-common-api/unauthorized")
    assert r_unauth.status_code == 401
    assert r_unauth.json()["error"]["code"] == "UNAUTHORIZED"

    r_forbid = client.get("/test-common-api/forbidden")
    assert r_forbid.status_code == 403
    assert r_forbid.json()["error"]["code"] == "FORBIDDEN"


def test_service_unavailable_mapping(client: TestClient):
    """Verify ServiceUnavailableError returns HTTP 503."""
    response = client.get("/test-common-api/service-unavailable")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_pydantic_request_validation_error_handler(client: TestClient):
    """Verify Pydantic input validation failure returns formatted 422 error details."""
    response = client.post(
        "/test-common-api/pydantic-validation",
        json={"name": "a", "score": 150.0},  # name too short, score > 100
    )
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    err = data["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert err["status_code"] == 422
    assert isinstance(err["details"], list)
    fields = [d["field"] for d in err["details"]]
    assert "name" in fields
    assert "score" in fields


def test_http_exception_404_on_unknown_route(client: TestClient):
    """Verify standard Starlette HTTP 404 returns structured error response."""
    response = client.get("/non-existent-random-endpoint-xyz")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    err = data["error"]
    assert err["code"] == "NOT_FOUND"
    assert err["status_code"] == 404
    assert REQUEST_ID_HEADER in response.headers
    assert err["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_unexpected_exception_sanitization_and_no_leakage():
    """Verify unhandled exceptions return safe generic 500 error and do NOT leak secrets/SQL."""
    with TestClient(app, raise_server_exceptions=False) as unhandled_client:
        response = unhandled_client.get("/test-common-api/unhandled")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        err = data["error"]
        assert err["code"] == "INTERNAL_SERVER_ERROR"
        assert err["status_code"] == 500
        assert err["message"] == "An unexpected internal server error occurred."
        assert err["details"] is None
        # Verify no sensitive leaked content
        response_text = response.text
        assert "super_secret_password" not in response_text
        assert "Traceback" not in response_text
        assert "db:5432" not in response_text


def test_existing_endpoints_unaffected(client: TestClient):
    """Verify /health, /ready, /, and /api/v1 remain functional and include X-Request-ID."""
    for path, expected_status in [
        ("/health", 200),
        ("/ready", 200),
        ("/", 200),
        ("/api/v1", 200),
    ]:
        resp = client.get(path)
        assert resp.status_code == expected_status
        assert REQUEST_ID_HEADER in resp.headers


def test_openapi_schema_contains_error_response_models(client: TestClient):
    """Verify OpenAPI schema loads cleanly and documents ErrorResponse."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "components" in schema
    assert "schemas" in schema["components"]
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert "ErrorDetail" in schema["components"]["schemas"]
