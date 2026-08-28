"""Phase 0 gate: /api/health returns 200 with a token, 401 without."""
from __future__ import annotations


def test_health_ok_with_token(client, auth_headers):
    resp = client.get("/api/health", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "wifideck"
    assert "version" in body


def test_health_401_without_token(client):
    resp = client.get("/api/health")
    assert resp.status_code == 401


def test_health_401_with_wrong_token(client):
    resp = client.get("/api/health", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 401


def test_x_auth_token_header_also_works(client):
    resp = client.get("/api/health", headers={"X-Auth-Token": "test-token"})
    assert resp.status_code == 200
