"""Station parsing, OUI/randomization detection, tracker, and /api/stations."""
from __future__ import annotations

from app.models.station import Station
from app.services import fixtures
from app.services.stations import StationTracker, parse_airodump_stations, vendor_for


def test_vendor_randomized_and_oui():
    assert vendor_for("02:00:00:00:00:aa") == "randomized"  # locally-administered bit
    assert vendor_for("B8:27:EB:12:34:56") == "Raspberry Pi"
    assert vendor_for("F0:18:98:11:22:33") == "Apple"
    assert vendor_for("A4:B1:C2:00:00:00") is None  # unknown global OUI


def test_parse_stations():
    st = parse_airodump_stations(fixtures.AIRODUMP_CSV)
    a = next(s for s in st if s.mac == "02:00:00:00:00:AA")
    assert a.bssid == "02:00:00:00:00:01"
    assert a.vendor == "randomized"
    assert a.signal_dbm == -50


def test_tracker_merges():
    t = StationTracker()
    t.observe([Station(mac="02:00:00:00:00:AA", probes=["Home"], packets=10, last_seen="t1")])
    t.observe([Station(mac="02:00:00:00:00:AA", probes=["Cafe"], packets=25,
                       last_seen="t2", signal_dbm=-40)])
    lst = t.list()
    assert len(lst) == 1
    assert set(lst[0].probes) == {"Home", "Cafe"}
    assert lst[0].packets == 25 and lst[0].signal_dbm == -40


def test_stations_endpoint(client, auth_headers):
    assert client.get("/api/stations").status_code == 401
    r = client.get("/api/stations", headers=auth_headers)
    assert r.status_code == 200
    assert "02:00:00:00:00:AA" in {s["mac"] for s in r.json()}  # mock → fixture stations
