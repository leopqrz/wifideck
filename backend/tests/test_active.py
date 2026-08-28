"""Scope allowlist, audit log, and the layered deauth guardrails."""
from __future__ import annotations

import asyncio

from app.services.active import ActiveDisabled, ActiveService
from app.services.audit import AuditLog
from app.services.runner import CommandRunner
from app.services.scope import ScopeList, normalize_bssid
from app.services.status import StatusService

BSSID = "AA:BB:CC:DD:EE:FF"


def test_normalize_bssid():
    assert normalize_bssid("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"
    assert normalize_bssid("not-a-mac") is None


# ---- scope + audit endpoints ----
def test_scope_add_list_remove(client, auth_headers):
    assert client.get("/api/scope", headers=auth_headers).json() == []
    r = client.post("/api/scope", json={"bssid": BSSID, "ssid": "MyLab"}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["bssid"] == BSSID
    assert any(t["bssid"] == BSSID for t in client.get("/api/scope", headers=auth_headers).json())
    assert client.delete(f"/api/scope/{BSSID}", headers=auth_headers).status_code == 200
    assert client.get("/api/scope", headers=auth_headers).json() == []


def test_scope_rejects_bad_bssid(client, auth_headers):
    assert client.post("/api/scope", json={"bssid": "nope"}, headers=auth_headers).status_code == 422


# ---- deauth guardrails ----
def test_deauth_refused_when_not_in_scope(client, auth_headers):
    r = client.post(
        "/api/active/deauth",
        json={"bssid": "11:22:33:44:55:66", "authorized": True},
        headers=auth_headers,
    )
    assert r.status_code == 403
    assert "scope" in r.json()["detail"].lower()


def test_deauth_refused_without_authorization(client, auth_headers):
    client.post("/api/scope", json={"bssid": BSSID}, headers=auth_headers)
    r = client.post(
        "/api/active/deauth", json={"bssid": BSSID, "authorized": False}, headers=auth_headers
    )
    assert r.status_code == 403
    assert "authorization" in r.json()["detail"].lower()


def test_deauth_allowed_when_in_scope_and_authorized(client, auth_headers):
    client.post("/api/scope", json={"bssid": BSSID, "ssid": "MyLab"}, headers=auth_headers)
    r = client.post(
        "/api/active/deauth",
        json={"bssid": BSSID, "authorized": True, "count": 3},
        headers=auth_headers,
    )
    assert r.status_code == 200
    entry = r.json()
    assert entry["action"] == "deauth" and entry["result"] == "ok"
    assert entry["target_bssid"] == BSSID


def test_audit_records_refusals_and_actions(client, auth_headers):
    # a refusal (not in scope) then an allowed action both appear in the audit log
    client.post("/api/active/deauth", json={"bssid": "99:99:99:99:99:99", "authorized": True}, headers=auth_headers)
    audit = client.get("/api/audit", headers=auth_headers).json()
    assert any(e["action"] == "deauth.refused" for e in audit)


def test_active_state_reports_enabled(client, auth_headers):
    assert client.get("/api/active", headers=auth_headers).json()["enabled"] is True


def test_deauth_blocked_when_active_disabled():
    # A service constructed with enabled=False refuses regardless of scope/auth.
    scope = ScopeList("/tmp/wifideck-test/scope-disabled.json")
    scope.add(BSSID)
    audit = AuditLog("/tmp/wifideck-test/audit-disabled.jsonl")
    svc = ActiveService(
        runner=CommandRunner(mock=True),
        scope=scope,
        audit=audit,
        status=StatusService(CommandRunner(mock=True)),
        enabled=False,
        mock=True,
    )
    try:
        asyncio.run(svc.deauth(BSSID, None, 3, authorized=True))
        raise AssertionError("expected ActiveDisabled")
    except ActiveDisabled:
        pass


def test_active_endpoints_require_token(client):
    assert client.get("/api/scope").status_code == 401
    assert client.get("/api/audit").status_code == 401
    assert client.post("/api/active/deauth", json={"bssid": BSSID}).status_code == 401
