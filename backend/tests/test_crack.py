"""aircrack progress parser + crack guardrails + mock found-path."""
from __future__ import annotations

import asyncio

import pytest

from app.services.audit import AuditLog
from app.services.capture import CaptureService
from app.services.crack import (
    CrackNotFound,
    CrackRefused,
    CrackService,
    parse_aircrack_progress,
)
from app.services.runner import CommandRunner
from app.services.scope import ScopeList

BSSID = "02:00:00:00:00:01"

AIRCRACK_OUT = """Aircrack-ng 1.7
      [00:00:04] 4008/10303 keys tested (1002.50 k/s)
KEY FOUND! [ password123 ]
"""


def test_parse_progress_and_key():
    p = parse_aircrack_progress(AIRCRACK_OUT)
    assert p["tested"] == 4008
    assert p["total"] == 10303
    assert p["rate"] == 1002.50
    assert p["key"] == "password123"


def test_parse_progress_only():
    p = parse_aircrack_progress("[00:00:10] 5000/9999 keys tested (900.00 k/s)")
    assert p["tested"] == 5000
    assert "key" not in p


def _build(scoped: bool):
    cap = CaptureService(CommandRunner(mock=True), "/tmp/wifideck-test/crack-sessions", mock=True)
    session = asyncio.run(cap.start("wlan0", 157, BSSID))
    scope = ScopeList("/tmp/wifideck-test/crack-scope.json")
    if scoped:
        scope.add(BSSID)
    else:
        scope.remove(BSSID)
    audit = AuditLog("/tmp/wifideck-test/crack-audit.jsonl")
    svc = CrackService(cap, scope, audit, "/tmp/wordlist.txt", mock=True)
    return svc, session.id


def test_crack_found_in_mock():
    svc, _ = _build(scoped=True)
    asyncio.run(svc._run(BSSID, "/tmp/wordlist.txt", None))
    assert svc.state == "found"
    assert svc.key == "mock-passphrase"


def test_crack_refused_not_in_scope():
    svc, sid = _build(scoped=False)
    with pytest.raises(CrackRefused):
        asyncio.run(svc.start(sid, None, authorized=True))


def test_crack_refused_without_authorization():
    svc, sid = _build(scoped=True)
    with pytest.raises(CrackRefused):
        asyncio.run(svc.start(sid, None, authorized=False))


def test_crack_unknown_session():
    svc, _ = _build(scoped=True)
    with pytest.raises(CrackNotFound):
        asyncio.run(svc.start("no-such-session", None, authorized=True))


def test_crack_endpoint_guards(client, auth_headers):
    sid = client.post(
        "/api/capture", json={"channel": 157, "bssid": "02:00:00:00:00:AB"}, headers=auth_headers
    ).json()["id"]
    # target BSSID not in the shared scope allowlist -> 403
    r = client.post("/api/crack", json={"session_id": sid, "authorized": True}, headers=auth_headers)
    assert r.status_code == 403
    # unknown session -> 404
    assert client.post(
        "/api/crack", json={"session_id": "nope", "authorized": True}, headers=auth_headers
    ).status_code == 404


def test_crack_requires_token(client):
    assert client.get("/api/crack").status_code == 401
    assert client.post("/api/crack", json={"session_id": "x"}).status_code == 401
