"""Security-posture classifier + assessment report (aggregate, HTML, endpoints)."""
from __future__ import annotations

from app.models.network import Network
from app.models.session import CaptureSession
from app.services import report as report_svc
from app.services.audit import AuditLog
from app.services.history import HistoryStore
from app.services.known import KnownNetworks
from app.services.posture import classify_security
from app.services.scope import ScopeList


def test_posture_classes():
    assert classify_security([]).kind == "open"
    assert classify_security(["WEP"]).kind == "wep"
    assert classify_security(["WPA2"]).kind == "wpa2"
    assert classify_security(["SAE"]).kind == "wpa3"
    assert classify_security(["802.1X"]).kind == "enterprise"
    t = classify_security(["WPA2", "WPA3"])
    assert t.kind == "wpa3-transition"
    assert "WPA2 fallback" in t.note


def _net(**kw) -> Network:
    base = dict(
        bssid="02:00:00:00:00:01", ssid="MockNet-5G", band="5 GHz", channel=157,
        signal_pct=70, signal_dbm=-50, security=["WPA2", "WPA3"], is_current=False, clients=0,
    )
    base.update(kw)
    return Network(**base)


def _stores(tmp_path):
    h = HistoryStore(str(tmp_path / "h.db"))
    a = AuditLog(str(tmp_path / "a.jsonl"))
    sc = ScopeList(str(tmp_path / "s.json"))
    kn = KnownNetworks(str(tmp_path / "k.json"))
    return h, a, sc, kn


def test_gather_and_render(tmp_path):
    h, a, sc, kn = _stores(tmp_path)
    kn.save([_net()])
    h.record_session(CaptureSession(
        id="20260830-000000", started="2026-08-30T00:00:00+00:00", mode="handshake",
        target_bssid="02:00:00:00:00:01", handshake=True, pcap_available=True,
    ))
    h.record_crack("20260830-000000", "hashcat", "found", "s3cret", "2026-08-30T00:05:00+00:00")
    sc.add("02:00:00:00:00:01", "MockNet-5G")
    a.record("deauth", "ok", target_bssid="02:00:00:00:00:01")

    r = report_svc.gather(h, a, sc, kn, "9.9.9")
    assert r.summary.networks == 1
    assert r.summary.sessions == 1
    assert r.summary.handshakes == 1
    assert r.summary.cracked == 1
    assert r.summary.scoped == 1
    assert r.networks[0].posture_label == "WPA3-TRANSITION"

    html = report_svc.render_html(r)
    for needle in ("WiFiDeck", "MockNet-5G", "WPA3-TRANSITION", "s3cret", "deauth"):
        assert needle in html


def test_report_endpoints(client, auth_headers):
    assert client.get("/api/report").status_code == 401
    r = client.get("/api/report", headers=auth_headers)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "WiFiDeck" in r.text
    d = client.get("/api/report/data", headers=auth_headers)
    assert d.status_code == 200
    assert "summary" in d.json()
