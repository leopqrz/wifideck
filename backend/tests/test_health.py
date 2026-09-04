"""Phase 0 gate: /api/health returns 200 with a token, 401 without."""
from __future__ import annotations


def test_health_ok_with_token(client, auth_headers):
    resp = client.get("/api/health", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "wifideck"
    assert "version" in body


def test_health_reports_host_os(client, auth_headers):
    body = client.get("/api/health", headers=auth_headers).json()
    # The app says which OS it runs on so the UI can show it plainly.
    assert body["os"] in {"macOS", "Linux", "Windows"} or isinstance(body["os"], str)
    assert body["os_detail"] and isinstance(body["os_detail"], str)
    assert isinstance(body["arch"], str)
    # mock fixtures -> mock backend; otherwise the OS-appropriate one.
    assert body["backend"] in {"mock", "linux-nl80211", "macos-rtl8812au"}


def test_health_401_without_token(client):
    resp = client.get("/api/health")
    assert resp.status_code == 401


def test_health_401_with_wrong_token(client):
    resp = client.get("/api/health", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 401


def test_x_auth_token_header_also_works(client):
    resp = client.get("/api/health", headers={"X-Auth-Token": "test-token"})
    assert resp.status_code == 200
