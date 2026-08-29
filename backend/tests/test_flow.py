"""Guided capture flow: guardrails + the full mock orchestration."""
from __future__ import annotations

import asyncio

import pytest

from app.services.active import ActiveService
from app.services.audit import AuditLog
from app.services.capture import CaptureService
from app.services.flow import CaptureFlowService, FlowRefused
from app.services.mode import ModeService
from app.services.runner import CommandRunner
from app.services.scope import ScopeList
from app.services.status import StatusService

BSSID = "02:00:00:00:00:01"


def build_flow(enabled: bool = True) -> CaptureFlowService:
    runner = CommandRunner(mock=True)
    status = StatusService(runner)
    scope = ScopeList("/tmp/wifideck-test/flow-scope.json")
    scope.add(BSSID, "MockNet-5G")
    audit = AuditLog("/tmp/wifideck-test/flow-audit.jsonl")
    active = ActiveService(runner, scope, audit, status, enabled=enabled, mock=True)
    mode = ModeService(runner, status)
    capture = CaptureService(runner, "/tmp/wifideck-test/flow-sessions", mock=True)
    return CaptureFlowService(mode, capture, active, scope, status, enabled=enabled, mock=True)


def test_flow_completes_with_handshake():
    svc = build_flow()
    asyncio.run(svc._run(BSSID, 157, count=8, timeout=5))
    assert svc.state == "done"
    assert svc.handshake is True
    assert svc.session_id is not None
    assert [s.name for s in svc.steps] == ["monitor", "capture", "deauth", "handshake", "cleanup"]
    assert all(s.done for s in svc.steps)  # every step marked complete


def test_flow_refused_not_in_scope():
    svc = build_flow()
    with pytest.raises(FlowRefused):
        asyncio.run(svc.start("DE:AD:BE:EF:00:99", 157, authorized=True, count=8, timeout=60))


def test_flow_refused_without_authorization():
    svc = build_flow()
    with pytest.raises(FlowRefused):
        asyncio.run(svc.start(BSSID, 157, authorized=False, count=8, timeout=60))


def test_flow_refused_when_active_disabled():
    svc = build_flow(enabled=False)
    with pytest.raises(FlowRefused):
        asyncio.run(svc.start(BSSID, 157, authorized=True, count=8, timeout=60))


def test_flow_endpoint_status_and_guards(client, auth_headers):
    assert client.get("/api/flow", headers=auth_headers).status_code == 200
    # target not in the shared scope allowlist -> 403
    r = client.post(
        "/api/flow",
        json={"bssid": "DE:AD:BE:EF:00:98", "channel": 157, "authorized": True},
        headers=auth_headers,
    )
    assert r.status_code == 403


def test_flow_requires_token(client):
    assert client.get("/api/flow").status_code == 401
    assert client.post("/api/flow", json={"bssid": BSSID, "channel": 1}).status_code == 401
