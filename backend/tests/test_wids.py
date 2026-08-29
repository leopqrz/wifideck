"""WIDS-lite evil-twin detector + endpoints."""
from __future__ import annotations

from app.models.network import Network
from app.services.wids import find_evil_twins


def _n(ssid, bssid, security):
    return Network(ssid=ssid, bssid=bssid, security=security)


def test_evil_twin_flagged_on_mismatched_security():
    # same SSID, one WPA2 + one OPEN -> classic evil twin
    nets = [
        _n("CorpNet", "AA:AA:AA:AA:AA:01", ["WPA2"]),
        _n("CorpNet", "BB:BB:BB:BB:BB:02", []),
    ]
    tw = find_evil_twins(nets)
    assert len(tw) == 1
    assert tw[0]["ssid"] == "CorpNet"
    assert tw[0]["severity"] == "high"


def test_enterprise_roaming_not_flagged():
    # same SSID on 3 BSSIDs, all WPA2 -> normal roaming, NOT an alert
    nets = [
        _n("CorpNet", "AA:AA:AA:AA:AA:01", ["WPA2"]),
        _n("CorpNet", "AA:AA:AA:AA:AA:02", ["WPA2"]),
        _n("CorpNet", "AA:AA:AA:AA:AA:03", ["WPA2"]),
    ]
    assert find_evil_twins(nets) == []


def test_distinct_ssids_not_flagged():
    nets = [
        _n("Alpha", "AA:AA:AA:AA:AA:01", ["WPA2"]),
        _n("Beta", "BB:BB:BB:BB:BB:02", []),
    ]
    assert find_evil_twins(nets) == []


def test_single_bssid_not_flagged():
    assert find_evil_twins([_n("Solo", "AA:AA:AA:AA:AA:01", ["WPA2"])]) == []


def test_endpoint_status_and_toggle(client, auth_headers):
    assert client.get("/api/wids", headers=auth_headers).status_code == 200
    on = client.post("/api/wids", json={"enabled": True}, headers=auth_headers).json()
    assert on["running"] is True
    off = client.post("/api/wids", json={"enabled": False}, headers=auth_headers).json()
    assert off["running"] is False


def test_wids_requires_token(client):
    assert client.get("/api/wids").status_code == 401
