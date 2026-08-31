"""Roles: operator vs viewer, /api/me, and the read-only middleware."""
from __future__ import annotations

from app.auth import role_for_token
from app.config import settings


def test_role_for_token():
    assert role_for_token(settings.token) == "operator"
    assert role_for_token("nope") is None
    assert role_for_token(None) is None


def test_me_operator(client, auth_headers):
    r = client.get("/api/me", headers=auth_headers)
    assert r.status_code == 200 and r.json()["role"] == "operator"


def test_me_requires_token(client):
    assert client.get("/api/me").status_code == 401


def test_viewer_is_read_only(client):
    # Turn on RBAC by setting a viewer token (frozen dataclass -> bypass setattr).
    object.__setattr__(settings, "viewer_token", "viewer-tok")
    try:
        vh = {"Authorization": "Bearer viewer-tok"}
        assert client.get("/api/me", headers=vh).json()["role"] == "viewer"
        assert client.get("/api/status", headers=vh).status_code == 200  # GET ok
        # mutating request is blocked for the viewer
        assert client.post("/api/mode", json={"mode": "managed"}, headers=vh).status_code == 403
    finally:
        object.__setattr__(settings, "viewer_token", "")
