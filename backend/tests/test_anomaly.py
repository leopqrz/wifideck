"""Device anomaly / risk scoring."""
from __future__ import annotations

from app.models.station import Station
from app.services.anomaly import score_station


def test_trackable_prober_scores_high():
    s = Station(mac="AA:BB:CC:DD:EE:FF", vendor="Apple",
                probes=["A", "B", "C", "D", "E"], bssid=None, packets=50)
    score, reasons = score_station(s)
    assert score >= 3 and reasons  # stable MAC + many probes + chatty-unassociated


def test_randomized_associated_is_quiet():
    s = Station(mac="02:00:00:00:00:aa", vendor="randomized",
                probes=[], bssid="02:00:00:00:00:01", packets=40)
    assert score_station(s)[0] == 0


def test_anomaly_endpoint(client, auth_headers):
    assert client.get("/api/anomalies").status_code == 401
    r = client.get("/api/anomalies", headers=auth_headers)
    assert r.status_code == 200 and isinstance(r.json(), list)
