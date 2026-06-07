"""Shared fixtures for backend tests."""
from pathlib import Path
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so "import backend" works,
# making relative imports in backend/main.py resolve correctly.
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session", autouse=True)
def _set_env():
    """Set GENOMA_SESSION_TOKEN once before any tests are collected/run."""
    os.environ["GENOMA_SESSION_TOKEN"] = "test-token-for-tests"
    yield


@pytest.fixture(scope="session")
def app():
    """FastAPI application instance (session-scoped, imported once)."""
    from backend.main import app as _app
    return _app


@pytest.fixture
def client(app):
    """FastAPI TestClient wrapping the application."""
    with TestClient(app) as c:
        yield c
