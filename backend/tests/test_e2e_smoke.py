"""End-to-end smoke test: walk the whole stack via the API in mock mode. If this
passes, every subsystem is wired together (mode → capture → verify → history →
report → stations → schedule → metrics → wids → rbac)."""
from __future__ import annotations


def test_full_stack_smoke(client, auth_headers):
    h = auth_headers

    # identity + status
    assert client.get("/api/me", headers=h).json()["role"] == "operator"
    assert client.get("/api/status", headers=h).status_code == 200

    # mode switch reflects in status (mock)
    assert client.post("/api/mode", json={"mode": "monitor"}, headers=h).status_code == 200
    assert client.get("/api/status", headers=h).json()["mode"] == "MONITOR"

    # ensure no capture is mid-flight from another test (shared singleton)
    for s in client.get("/api/capture", headers=h).json():
        if s.get("running"):
            client.post(f"/api/capture/{s['id']}/stop", headers=h)

    # PMKID capture → detected, then verify + stop
    sid = client.post("/api/capture", json={"mode": "pmkid"}, headers=h).json()["id"]
    assert client.get(f"/api/capture/{sid}", headers=h).json()["pmkid"] is True
    assert client.get(f"/api/capture/{sid}/handshake", headers=h).status_code == 200
    client.post(f"/api/capture/{sid}/stop", headers=h)

    # persisted to history
    assert any(e["id"] == sid for e in client.get("/api/history", headers=h).json())

    # reporting, stations, scheduling, metrics, wids baseline
    assert "WiFiDeck" in client.get("/api/report", headers=h).text
    assert client.get("/api/stations", headers=h).status_code == 200
    assert "scan" in {j["id"] for j in client.get("/api/schedule", headers=h).json()}
    assert "wifideck_up 1" in client.get("/metrics", headers=h).text
    assert client.post("/api/wids/baseline", headers=h).json()["baseline"] >= 0

    # back to managed
    assert client.post("/api/mode", json={"mode": "managed"}, headers=h).status_code == 200
    assert client.get("/api/status", headers=h).json()["mode"] == "MANAGED"
