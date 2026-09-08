import os
import sys

# Ensure backend root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a test client for FastAPI application endpoints."""
    with TestClient(app) as test_client:
        yield test_client
