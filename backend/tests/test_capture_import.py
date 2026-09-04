"""Import an external pcap (e.g. from the macOS libusb capture) as a session."""
from __future__ import annotations


def test_import_pcap(client, auth_headers, tmp_path):
    p = tmp_path / "ext.pcap"
    p.write_bytes(b"\xd4\xc3\xb2\xa1\x02\x00\x04\x00")  # pcap magic + a few bytes
    r = client.post(
        "/api/capture/import",
        json={"path": str(p), "bssid": "02:00:00:00:00:01", "channel": 6},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "import" and body["pcap_available"] is True
    sid = body["id"]
    ids = [s["id"] for s in client.get("/api/capture", headers=auth_headers).json()]
    assert sid in ids  # shows up as a normal session → crackable


def test_import_missing_pcap(client, auth_headers):
    r = client.post("/api/capture/import", json={"path": "/nope/x.pcap"}, headers=auth_headers)
    assert r.status_code == 400


def test_import_requires_token(client):
    assert client.post("/api/capture/import", json={"path": "/x"}).status_code == 401
