"""macOS monitor-scan endpoint (returns [] on non-macos backends like mock)."""
from __future__ import annotations


def test_scan_once_mock_returns_empty(client, auth_headers):
    r = client.post("/api/scan/once?channel=6&seconds=2", headers=auth_headers)
    assert r.status_code == 200 and r.json() == []  # mock backend → no macOS scan


def test_scan_once_requires_token(client):
    assert client.post("/api/scan/once").status_code == 401
