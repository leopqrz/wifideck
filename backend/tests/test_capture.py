"""Capture handshake parser + /api/capture lifecycle (mock mode)."""
from __future__ import annotations

from app.services.capture import parse_aircrack_handshakes

AIRCRACK_OUT = """Reading packets, please wait...
   #  BSSID              ESSID                     Encryption
   1  96:04:E3:EC:AB:5A  Queiroz                   WPA (1 handshake)
   2  58:CB:52:DE:18:41  High-Five Wifi            WPA (0 handshake)
"""

AIRCRACK_PMKID = """
   1  96:04:E3:EC:AB:5A  Queiroz                   WPA (1 handshake, with PMKID)
"""


def test_parse_handshake():
    flags = parse_aircrack_handshakes(AIRCRACK_OUT, "96:04:E3:EC:AB:5A")
    assert flags["handshake"] is True
    assert flags["pmkid"] is False


def test_parse_pmkid():
    flags = parse_aircrack_handshakes(AIRCRACK_PMKID)
    assert flags["handshake"] is True
    assert flags["pmkid"] is True


def test_parse_scoped_to_target():
    # handshake belongs to a different BSSID than the target -> not counted
    flags = parse_aircrack_handshakes(AIRCRACK_OUT, "58:CB:52:DE:18:41")
    assert flags["handshake"] is False


def test_capture_lifecycle(client, auth_headers):
    # start
    r = client.post("/api/capture", json={"channel": 157}, headers=auth_headers)
    assert r.status_code == 200
    sid = r.json()["id"]
    assert r.json()["running"] is True

    # a second start while running is rejected
    assert client.post("/api/capture", json={}, headers=auth_headers).status_code == 409

    # list contains it
    ids = [s["id"] for s in client.get("/api/capture", headers=auth_headers).json()]
    assert sid in ids

    # detail carries live networks + handshake flag (from mock fixture)
    detail = client.get(f"/api/capture/{sid}", headers=auth_headers).json()
    assert detail["ap_count"] >= 1
    assert detail["handshake"] is True
    assert len(detail["networks"]) >= 1

    # stop
    stopped = client.post(f"/api/capture/{sid}/stop", headers=auth_headers).json()
    assert stopped["running"] is False


def test_capture_requires_token(client):
    assert client.post("/api/capture", json={}).status_code == 401


def test_pcap_unknown_session_404(client, auth_headers):
    assert client.get("/api/capture/nope/pcap", headers=auth_headers).status_code == 404
