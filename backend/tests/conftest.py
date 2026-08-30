"""Test fixtures. Sets a known token BEFORE importing the app so config picks
it up, then exposes an authenticated and an anonymous client."""
from __future__ import annotations

import os

os.environ["WIFIDECK_TOKEN"] = "test-token"
os.environ["WIFIDECK_HOST"] = "127.0.0.1"
# Tests never touch real hardware: mock mode feeds recorded fixtures.
os.environ["WIFIDECK_MOCK"] = "1"
os.environ["WIFIDECK_CAPTURE_DIR"] = "/tmp/wifideck-test/sessions"
# Active modules enabled so tests can exercise the gated path; fresh scope+audit.
os.environ["WIFIDECK_ENABLE_ACTIVE"] = "1"
os.environ["WIFIDECK_SCOPE_FILE"] = "/tmp/wifideck-test/scope.json"
os.environ["WIFIDECK_AUDIT_LOG"] = "/tmp/wifideck-test/audit.jsonl"
os.environ["WIFIDECK_DB"] = "/tmp/wifideck-test/wifideck.db"
for _p in (
    "/tmp/wifideck-test/scope.json",
    "/tmp/wifideck-test/audit.jsonl",
    "/tmp/wifideck-test/wifideck.db",
):
    try:
        os.remove(_p)
    except OSError:
        pass

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import fixtures

TOKEN = "test-token"


@pytest.fixture(autouse=True)
def _reset_mock_mode():
    """Mock adapter mode is process-global; reset it so tests don't leak state."""
    fixtures.reset_mock_mode()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": f"Bearer {TOKEN}"}
