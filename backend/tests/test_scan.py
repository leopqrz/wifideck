"""Scan parser + /ws/scan tests."""
from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect

from app.services import scan
from app.services.fixtures import NMCLI_WIFI

AIRODUMP_CSV = """
BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key

96:04:E3:EC:AB:5A, 2026-08-28 03:00:00, 2026-08-28 03:05:00, 157, 866, WPA2, CCMP, PSK, -42, 120, 0, 0. 0. 0. 0, 7, Queiroz,
58:CB:52:DE:18:41, 2026-08-28 03:00:00, 2026-08-28 03:05:00,   6, 130, WPA2, CCMP, PSK, -70, 60, 0, 0. 0. 0. 0, 14, High-Five Wifi,

Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
AA:BB:CC:DD:EE:FF, 2026-08-28 03:00:00, 2026-08-28 03:05:00, -50, 40, 96:04:E3:EC:AB:5A,
11:22:33:44:55:66, 2026-08-28 03:00:00, 2026-08-28 03:05:00, -60, 12, 96:04:E3:EC:AB:5A,
"""


def test_parse_nmcli_wifi():
    nets = scan.parse_nmcli_wifi(NMCLI_WIFI)
    assert len(nets) == 4
    cur = next(n for n in nets if n.is_current)
    assert cur.ssid == "Queiroz"
    assert cur.bssid == "96:04:E3:EC:AB:5A"
    assert cur.channel == 157
    assert cur.band == "5 GHz"
    assert cur.signal_pct == 100
    assert cur.security == ["WPA2", "WPA3"]
    # hidden SSID becomes None
    assert any(n.ssid is None for n in nets)


def test_parse_airodump_csv():
    nets = scan.parse_airodump_csv(AIRODUMP_CSV)
    assert len(nets) == 2
    q = next(n for n in nets if n.ssid == "Queiroz")
    assert q.channel == 157
    assert q.signal_dbm == -42
    assert q.signal_pct == 80  # (-42+90)/60*100
    assert q.clients == 2      # two stations associated
    assert "WPA2" in q.security


def test_band_for_channel():
    assert scan.band_for_channel(6) == "2.4 GHz"
    assert scan.band_for_channel(157) == "5 GHz"
    assert scan.band_for_channel(None) is None


def test_ws_scan_managed_mock(client):
    with client.websocket_connect("/ws/scan?token=test-token") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "scan"
        assert msg["source"] == "managed"
        ssids = [n["ssid"] for n in msg["data"]]
        assert "Queiroz" in ssids


def test_ws_scan_requires_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/scan?token=bad") as ws:
            ws.receive_json()
