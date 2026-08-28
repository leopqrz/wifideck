"""Internet-sharing parsers + /api/share (mock mode)."""
from __future__ import annotations

from app.services.share import mac_commands, parse_default_gateway


def test_parse_default_gateway():
    assert parse_default_gateway("default via 192.0.2.1 dev wlan0 metric 600") == "192.0.2.1"
    assert parse_default_gateway("no default here") is None


def test_mac_commands_use_vm_ip():
    cmds = mac_commands("192.0.2.128")
    assert any("192.0.2.128" in c for c in cmds)
    assert any("setdnsservers" in c for c in cmds)


def test_share_status_reports_topology(client, auth_headers):
    r = client.get("/api/share", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["downlink"] == "eth0"
    assert d["uplink"] == "wlan0"
    assert d["vm_ip"] == "192.0.2.128"
    assert any("192.0.2.128" in c for c in d["mac_commands"])


def test_share_toggle(client, auth_headers):
    on = client.post("/api/share", json={"enabled": True}, headers=auth_headers).json()
    assert on["active"] is True
    off = client.post("/api/share", json={"enabled": False}, headers=auth_headers).json()
    assert off["active"] is False


def test_share_requires_token(client):
    assert client.get("/api/share").status_code == 401
    assert client.post("/api/share", json={"enabled": True}).status_code == 401
