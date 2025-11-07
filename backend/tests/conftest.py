"""
Pytest Configuration and Fixtures

Shared test fixtures for backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    """FastAPI test client fixture"""
    return TestClient(app)
