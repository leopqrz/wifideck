"""SQLite history store + /api/history endpoint."""
from __future__ import annotations

from app.models.session import CaptureSession
from app.services.history import HistoryStore

SID = "20260830-000000"


def _sess(**kw) -> CaptureSession:
    base = dict(
        id=SID, started="2026-08-30T00:00:00+00:00", mode="pmkid",
        target_bssid="02:00:00:00:00:01", pcap_available=True,
    )
    base.update(kw)
    return CaptureSession(**base)


def test_record_and_query(tmp_path):
    db = HistoryStore(str(tmp_path / "h.db"))
    db.record_session(_sess())
    db.record_crack(SID, "hashcat", "found", "s3cret", "2026-08-30T00:05:00+00:00")
    rows = db.entries()
    assert len(rows) == 1
    e = rows[0]
    assert e.id == SID and e.mode == "pmkid"
    assert e.crack_engine == "hashcat" and e.crack_key == "s3cret" and e.crack_state == "found"


def test_latest_crack_wins(tmp_path):
    db = HistoryStore(str(tmp_path / "h.db"))
    db.record_session(_sess())
    db.record_crack(SID, "aircrack", "exhausted", None, "2026-08-30T00:01:00+00:00")
    db.record_crack(SID, "hashcat", "found", "pw", "2026-08-30T00:09:00+00:00")
    e = db.entries()[0]
    assert e.crack_state == "found" and e.crack_key == "pw"


def test_upsert_updates_session(tmp_path):
    db = HistoryStore(str(tmp_path / "h.db"))
    db.record_session(_sess(handshake=False))
    db.record_session(_sess(handshake=True))
    rows = db.entries()
    assert len(rows) == 1 and rows[0].handshake is True


def test_history_endpoint(client, auth_headers):
    # Record straight into the shared store (avoids racing the capture singleton),
    # then read it back through the endpoint.
    from app.deps import get_history_store

    get_history_store().record_session(_sess(id="hist-endpoint-1"))
    hist = client.get("/api/history", headers=auth_headers).json()
    assert any(e["id"] == "hist-endpoint-1" for e in hist)


def test_history_requires_token(client):
    assert client.get("/api/history").status_code == 401
