"""WIDS baseline: rogue-AP + downgrade detection and the baseline endpoints."""
from __future__ import annotations

from app.models.network import Network
from app.services.wids import detect_downgrades, detect_rogue_aps


def _n(bssid, ssid, security) -> Network:
    return Network(
        bssid=bssid, ssid=ssid, band=None, channel=None, signal_pct=None,
        signal_dbm=None, security=security, is_current=False, clients=0,
    )


BASE = {"AA:AA:AA:AA:AA:AA": {"ssid": "Home", "security": ["WPA2"]}}


def test_rogue_ap_detection():
    nets = [_n("AA:AA:AA:AA:AA:AA", "Home", ["WPA2"]), _n("BB:BB:BB:BB:BB:BB", "Evil", ["WPA2"])]
    r = detect_rogue_aps(nets, BASE)
    assert len(r) == 1 and r[0]["bssid"] == "BB:BB:BB:BB:BB:BB"
    assert detect_rogue_aps(nets, {}) == []  # no baseline -> no rogue alerts


def test_downgrade_detection():
    assert detect_downgrades([_n("AA:AA:AA:AA:AA:AA", "Home", [])], BASE)[0]["severity"] == "high"
    assert detect_downgrades([_n("AA:AA:AA:AA:AA:AA", "Home", ["WPA2"])], BASE) == []


def test_baseline_endpoints(client, auth_headers):
    assert client.post("/api/wids/baseline").status_code == 401
    r = client.post("/api/wids/baseline", headers=auth_headers)
    assert r.status_code == 200 and r.json()["baseline"] >= 1
    c = client.delete("/api/wids/baseline", headers=auth_headers)
    assert c.status_code == 200 and c.json()["baseline"] == 0
