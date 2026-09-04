"""Pytest configuration and fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a test client for FastAPI application endpoints."""
    with TestClient(app) as test_client:
        yield test_client
